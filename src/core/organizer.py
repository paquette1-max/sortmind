"""
File organizer - executes file organization operations safely.
"""
import shutil
import logging
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .config import OrganizationConfig, FileAnalysisResult, OrganizationPlan
from .scanner import ScannedFile

logger = logging.getLogger(__name__)


@dataclass
class FileOperation:
    """Represents a single file operation."""
    source: Path
    destination: Path
    operation_type: str  # 'move', 'rename', 'copy'
    confidence: float
    reasoning: str
    category: str
    original_name: str
    suggested_name: str


@dataclass
class ExecutionResult:
    """Result of executing an organization plan."""
    success: bool
    operations_completed: int
    operations_failed: int
    errors: List[str] = field(default_factory=list)
    batch_id: str = ""
    execution_time: float = 0.0


class FileOrganizer:
    """Organizes files based on LLM analysis results."""
    
    def __init__(
        self,
        config: Optional[OrganizationConfig] = None,
        undo_manager: Optional['UndoManager'] = None,
        backup_manager: Optional['BackupManager'] = None
    ):
        """
        Initialize file organizer.
        
        Args:
            config: Organization configuration
            undo_manager: Optional undo manager for tracking operations
            backup_manager: Optional backup manager for safety copies
        """
        # Allow being constructed with no args for test compatibility
        self.config = config or OrganizationConfig()
        self.undo_manager = undo_manager
        self.backup_manager = backup_manager
        self.logger = logger
    
    def create_organization_plan(
        self,
        scanned_files: List[ScannedFile],
        analysis_results: List[FileAnalysisResult],
        base_directory: Path
    ) -> OrganizationPlan:
        """
        Create a plan for organizing files.
        
        Args:
            scanned_files: List of scanned files
            analysis_results: LLM analysis results
            base_directory: Base directory for organization
        
        Returns:
            OrganizationPlan with proposed operations
        """
        logger.info(f"Creating organization plan for {len(scanned_files)} files")

        # Support legacy test format where analysis_results are dicts
        # Build a mapping from scanned file path (Path) -> result dict/object
        results_map = {}
        for res in analysis_results:
            # res can be a dict with keys like 'file_path' or an object
            if isinstance(res, dict):
                key = Path(res.get('file_path')) if res.get('file_path') else None
            else:
                # Try attribute access
                key = getattr(res, 'original_path', None) or getattr(res, 'file_path', None)
            if key:
                results_map[str(key)] = res

        ops = []
        for scanned in scanned_files:
            key = str(scanned if isinstance(scanned, Path) else getattr(scanned, 'path', scanned.path if hasattr(scanned, 'path') else scanned))
            result = results_map.get(key)
            if not result:
                logger.debug(f"No analysis result for {key}")
                continue

            # Unify result fields
            if isinstance(result, dict):
                confidence = float(result.get('confidence', 0.0))
                suggested_category = result.get('category') or result.get('suggested_category')
                suggested_filename = result.get('suggested_name') or result.get('suggested_filename')
                reasoning = result.get('reasoning', '')
            else:
                confidence = float(getattr(result, 'confidence', 0.0))
                suggested_category = getattr(result, 'suggested_category', None)
                suggested_filename = getattr(result, 'suggested_filename', None)
                reasoning = getattr(result, 'reasoning', '')

            # Skip low confidence if configured
            if confidence < self.config.confidence_threshold:
                logger.debug(f"Skipping {key} due to low confidence {confidence}")
                continue

            # Build destination Path
            category_path = Path(base_directory) / (suggested_category or 'uncategorized')
            destination = category_path / (suggested_filename or Path(key).name)

            # Preserve extension
            src_path = Path(key)
            if self.config.preserve_extensions and destination.suffix != src_path.suffix:
                destination = destination.with_suffix(src_path.suffix)

            # Truncate long names
            if len(destination.name) > self.config.max_filename_length:
                stem = destination.stem[: self.config.max_filename_length - len(destination.suffix) - 3]
                destination = destination.with_name(stem + '...' + destination.suffix)

            op = {
                'source': src_path,
                'destination': destination,
                'operation_type': 'move',
                'confidence': confidence,
                'reasoning': reasoning,
            }
            ops.append(op)

        plan = {
            'batch_id': str(uuid.uuid4()),
            'source_dir': Path(scanned_files[0]).parent if scanned_files else Path(base_directory),
            'target_dir': Path(base_directory),
            'operations': ops,
            'total_files': len(scanned_files),
            'processed_files': len(ops)
        }

        logger.info(f"Created plan with {len(ops)} operations")
        return plan
    
    def validate_plan(self, plan: OrganizationPlan) -> List[str]:
        """
        Validate organization plan for issues.
        
        Args:
            plan: Organization plan to validate
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Support both dict-style plan and object-style
        ops = plan.get('operations') if isinstance(plan, dict) else getattr(plan, 'file_operations', [])

        # Check for conflicts (multiple files to same destination)
        destinations = {}
        for op in ops:
            dest = op.get('destination') if isinstance(op, dict) else op.destination
            if dest in destinations:
                prev = destinations[dest]
                errors.append(f"Conflict: Multiple files targeting {dest}")
            destinations[dest] = op
        
        # Check for system directory targets
        system_dirs = {'/System', '/Library', '/Applications', '/usr', '/bin', '/etc'}
        for op in ops:
            dest = op.get('destination') if isinstance(op, dict) else op.destination
            for sys_dir in system_dirs:
                if str(dest).startswith(sys_dir):
                    errors.append(f"Invalid destination: Cannot organize into system directory {dest}")
                    break
        
        # Check for permission issues (basic check)
        for op in ops:
            source = op.get('source') if isinstance(op, dict) else op.source
            dest = op.get('destination') if isinstance(op, dict) else op.destination
            # Check source is readable
            if not Path(source).exists():
                errors.append(f"Source file not found: {source}")
            elif not os.access(str(source), os.R_OK):
                errors.append(f"No read permission: {source}")

            dest_parent = Path(dest).parent
            if dest_parent.exists():
                if not os.access(str(dest_parent), os.W_OK):
                    errors.append(f"No write permission: {dest_parent}")
        
        # Check disk space (approximate)
        try:
            total_size = sum(Path(op.get('source') if isinstance(op, dict) else op.source).stat().st_size
                             for op in ops if Path(op.get('source') if isinstance(op, dict) else op.source).exists())

            target_dir = plan.get('target_dir') if isinstance(plan, dict) else getattr(plan, 'target_dir', None)
            if target_dir and Path(target_dir).exists():
                import shutil as sh
                stat = sh.disk_usage(str(target_dir))
                if stat.free < total_size * 1.1:
                    errors.append(
                        f"Insufficient disk space. Need ~{total_size / (1024**3):.2f}GB, "
                        f"available {stat.free / (1024**3):.2f}GB"
                    )
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
        
        return errors
    
    def resolve_conflicts(self, plan: OrganizationPlan) -> OrganizationPlan:
        """
        Resolve filename conflicts by appending numbers.
        
        Args:
            plan: Organization plan with potential conflicts
        
        Returns:
            Updated plan with conflicts resolved
        """
        # Track used destinations
        used_destinations = set()
        resolved_operations = []

        ops = plan.get('operations') if isinstance(plan, dict) else getattr(plan, 'file_operations', [])

        for op in ops:
            # support dict-style or object-style op
            dest = op.get('destination') if isinstance(op, dict) else op.destination

            # If destination already used or exists, find unique name
            if dest in used_destinations or Path(dest).exists():
                counter = 1
                stem = Path(dest).stem
                suffix = Path(dest).suffix
                parent = Path(dest).parent

                while True:
                    new_name = f"{stem} ({counter}){suffix}"
                    new_dest = parent / new_name
                    if new_dest not in used_destinations and not new_dest.exists():
                        dest = new_dest
                        break

                    counter += 1
                    if counter > 1000:
                        logger.error(f"Could not resolve conflict for {op.get('source') if isinstance(op, dict) else op.source}")
                        break

                logger.info(f"Resolved conflict: {op.get('destination') if isinstance(op, dict) else op.destination} → {dest}")
                # assign back
                if isinstance(op, dict):
                    op['destination'] = dest
                else:
                    op.destination = dest

            used_destinations.add(dest)
            resolved_operations.append(op)

        if isinstance(plan, dict):
            plan['operations'] = resolved_operations
        else:
            plan.file_operations = resolved_operations

        return plan
    
    def execute_plan(
        self,
        plan: OrganizationPlan,
        dry_run: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> ExecutionResult:
        """
        Execute organization plan.
        
        Args:
            plan: Organization plan to execute
            dry_run: If True, only simulate execution
            progress_callback: Optional callback for progress updates
        
        Returns:
            ExecutionResult with operation status
        """
        start_time = datetime.now()
        batch_id = str(uuid.uuid4())

        ops = plan.get('operations') if isinstance(plan, dict) else getattr(plan, 'file_operations', [])

        logger.info(
            f"{'DRY RUN: ' if dry_run else ''}Executing plan "
            f"with {len(ops)} operations (batch {batch_id})"
        )
        
        # Validate plan first
        validation_errors = self.validate_plan(plan)
        if validation_errors:
            logger.error(f"Plan validation failed: {validation_errors}")
            return ExecutionResult(
                success=False,
                operations_completed=0,
                operations_failed=len(ops),
                errors=validation_errors,
                batch_id=batch_id
            )
        
        # Resolve conflicts
        plan = self.resolve_conflicts(plan)
        ops = plan.get('operations') if isinstance(plan, dict) else getattr(plan, 'file_operations', [])
        
        # Create backup if enabled and not dry run
        if not dry_run and self.backup_manager:
            try:
                source_files = [op.get('source') if isinstance(op, dict) else op.source for op in ops]
                backup_path = self.backup_manager.create_backup(source_files, batch_id)
                logger.info(f"Created backup at {backup_path}")
            except Exception as e:
                logger.error(f"Backup creation failed: {e}")
                return ExecutionResult(
                    success=False,
                    operations_completed=0,
                    operations_failed=len(ops),
                    errors=[f"Backup failed: {str(e)}"],
                    batch_id=batch_id
                )
        
        # Execute operations
        completed = 0
        failed = 0
        errors = []
        
        for idx, operation in enumerate(ops):
            try:
                # unify access
                src = operation.get('source') if isinstance(operation, dict) else operation.source
                dst = operation.get('destination') if isinstance(operation, dict) else operation.destination

                if dry_run:
                    logger.info(f"[DRY RUN] Would move {src} → {dst}")
                else:
                    Path(dst).parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(src), str(dst))
                    logger.info(f"Moved {src} → {dst}")

                    if self.undo_manager:
                        self.undo_manager.record_operation(
                            batch_id=batch_id,
                            operation_type='move',
                            source_path=src,
                            target_path=dst
                        )
                
                completed += 1
                
            except Exception as e:
                logger.error(f"Failed to move {operation.source}: {e}")
                errors.append(f"{operation.source.name}: {str(e)}")
                failed += 1
            
            # Progress callback
            if progress_callback:
                progress_callback(idx + 1, len(ops))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        
        result = ExecutionResult(
            success=(failed == 0),
            operations_completed=completed,
            operations_failed=failed,
            errors=errors,
            batch_id=batch_id,
            execution_time=execution_time
        )
        
        logger.info(
            f"Plan execution {'completed' if result.success else 'finished with errors'}: "
            f"{completed} succeeded, {failed} failed in {execution_time:.2f}s"
        )
        
        return result


import os  # For os.access checks