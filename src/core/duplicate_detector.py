"""
Duplicate file detection module.
Supports hash-based exact duplicate detection and perceptual hashing for similar images.
"""
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from collections import defaultdict
from enum import Enum

logger = logging.getLogger(__name__)


class DuplicateType(Enum):
    """Types of duplicate detection."""
    EXACT = "exact"  # Byte-for-byte identical
    SIMILAR = "similar"  # Perceptually similar (images)


@dataclass
class DuplicateGroup:
    """A group of duplicate files."""
    group_id: str
    duplicate_type: DuplicateType
    files: List[Path] = field(default_factory=list)
    hash_value: Optional[str] = None
    similarity_score: Optional[float] = None
    
    def add_file(self, file_path: Path) -> None:
        """Add a file to the group."""
        if file_path not in self.files:
            self.files.append(file_path)
    
    def remove_file(self, file_path: Path) -> bool:
        """Remove a file from the group."""
        if file_path in self.files:
            self.files.remove(file_path)
            return True
        return False
    
    def get_total_size(self) -> int:
        """Get total size of all files in the group."""
        total = 0
        for file_path in self.files:
            try:
                total += file_path.stat().st_size
            except:
                pass
        return total
    
    def get_wasted_space(self) -> int:
        """Get wasted space (total size minus one copy)."""
        if len(self.files) <= 1:
            return 0
        
        # Get size of first file (assuming all are same size for exact duplicates)
        try:
            file_size = self.files[0].stat().st_size
            return file_size * (len(self.files) - 1)
        except:
            return 0


@dataclass
class DuplicateDetectionResult:
    """Result of duplicate detection scan."""
    exact_duplicates: List[DuplicateGroup] = field(default_factory=list)
    similar_images: List[DuplicateGroup] = field(default_factory=list)
    scanned_files: int = 0
    scan_duration: float = 0.0
    
    @property
    def total_duplicates(self) -> int:
        """Get total number of duplicate files."""
        total = 0
        for group in self.exact_duplicates:
            total += len(group.files)
        for group in self.similar_images:
            total += len(group.files)
        return total
    
    @property
    def total_wasted_space(self) -> int:
        """Get total wasted space across all duplicates."""
        total = 0
        for group in self.exact_duplicates:
            total += group.get_wasted_space()
        for group in self.similar_images:
            total += group.get_wasted_space()
        return total
    
    @property
    def group_count(self) -> int:
        """Get total number of duplicate groups."""
        return len(self.exact_duplicates) + len(self.similar_images)


class DuplicateDetector:
    """Detects duplicate files using various methods."""
    
    # Common image formats for perceptual hashing
    IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif'}
    
    def __init__(self, 
                 hash_algorithm: str = 'blake2b',
                 chunk_size: int = 8192,
                 enable_perceptual_hash: bool = True,
                 similarity_threshold: int = 10):
        """
        Initialize duplicate detector.
        
        Args:
            hash_algorithm: Hash algorithm to use ('md5', 'sha256', 'blake2b')
            chunk_size: Size of chunks to read for hashing
            enable_perceptual_hash: Whether to enable perceptual hashing for images
            similarity_threshold: Hamming distance threshold for similar images (lower = more similar)
        """
        self.hash_algorithm = hash_algorithm
        self.chunk_size = chunk_size
        self.enable_perceptual_hash = enable_perceptual_hash
        self.similarity_threshold = similarity_threshold
        self.logger = logger
        
        # Cache for computed hashes
        self._hash_cache: Dict[Path, str] = {}
        self._perceptual_hash_cache: Dict[Path, str] = {}
    
    def find_duplicates(self, 
                       file_paths: List[Union[str, Path]],
                       detect_exact: bool = True,
                       detect_similar: bool = True,
                       progress_callback: Optional[callable] = None) -> DuplicateDetectionResult:
        """
        Find duplicate files in a list.
        
        Args:
            file_paths: List of file paths to check
            detect_exact: Whether to detect exact duplicates
            detect_similar: Whether to detect similar images
            progress_callback: Optional callback(current, total)
            
        Returns:
            DuplicateDetectionResult with all found duplicates
        """
        import time
        start_time = time.time()
        
        file_paths = [Path(p) for p in file_paths]
        result = DuplicateDetectionResult(scanned_files=len(file_paths))
        
        # Filter to existing files
        file_paths = [p for p in file_paths if p.exists()]
        
        if detect_exact:
            self.logger.info("Detecting exact duplicates...")
            result.exact_duplicates = self._find_exact_duplicates(
                file_paths, progress_callback
            )
        
        if detect_similar and self.enable_perceptual_hash:
            self.logger.info("Detecting similar images...")
            # Filter to images only
            image_paths = [p for p in file_paths 
                          if p.suffix.lower() in self.IMAGE_EXTENSIONS]
            result.similar_images = self._find_similar_images(
                image_paths, progress_callback
            )
        
        result.scan_duration = time.time() - start_time
        
        self.logger.info(
            f"Duplicate detection complete: "
            f"{len(result.exact_duplicates)} exact groups, "
            f"{len(result.similar_images)} similar groups, "
            f"{result.total_wasted_space / (1024*1024):.1f} MB wasted"
        )
        
        return result
    
    def _find_exact_duplicates(self, 
                               file_paths: List[Path],
                               progress_callback: Optional[callable] = None) -> List[DuplicateGroup]:
        """Find exact duplicates by content hash."""
        # Group by size first (optimization)
        size_groups: Dict[int, List[Path]] = defaultdict(list)
        
        for i, file_path in enumerate(file_paths):
            if progress_callback:
                progress_callback(i, len(file_paths) * 2)
            
            try:
                size = file_path.stat().st_size
                size_groups[size].append(file_path)
            except:
                continue
        
        # Now hash files that have the same size
        hash_groups: Dict[str, List[Path]] = defaultdict(list)
        
        processed = 0
        for size, paths in size_groups.items():
            if len(paths) < 2:
                continue  # Can't be duplicates if only one file
            
            for file_path in paths:
                if progress_callback:
                    progress_callback(len(file_paths) + processed, len(file_paths) * 2)
                processed += 1
                
                file_hash = self._compute_file_hash(file_path)
                if file_hash:
                    hash_groups[file_hash].append(file_path)
        
        # Create duplicate groups
        groups = []
        group_id = 0
        for file_hash, paths in hash_groups.items():
            if len(paths) > 1:
                group = DuplicateGroup(
                    group_id=f"exact_{group_id}",
                    duplicate_type=DuplicateType.EXACT,
                    files=paths.copy(),
                    hash_value=file_hash
                )
                groups.append(group)
                group_id += 1
        
        return groups
    
    def _find_similar_images(self,
                            image_paths: List[Path],
                            progress_callback: Optional[callable] = None) -> List[DuplicateGroup]:
        """Find similar images using perceptual hashing."""
        try:
            import imagehash
            from PIL import Image
        except ImportError:
            self.logger.warning("imagehash or PIL not installed. Skipping similar image detection.")
            return []
        
        # Compute perceptual hashes
        phashes: Dict[Path, imagehash.ImageHash] = {}
        
        for i, image_path in enumerate(image_paths):
            if progress_callback:
                progress_callback(i, len(image_paths) * 2)
            
            try:
                phash = self._compute_perceptual_hash(image_path)
                if phash is not None:
                    phashes[image_path] = phash
            except Exception as e:
                self.logger.debug(f"Failed to compute perceptual hash for {image_path}: {e}")
        
        # Group similar images
        similar_groups: List[List[Path]] = []
        processed: Set[Path] = set()
        
        for i, (path1, hash1) in enumerate(phashes.items()):
            if progress_callback:
                progress_callback(len(image_paths) + i, len(image_paths) * 2)
            
            if path1 in processed:
                continue
            
            group = [path1]
            processed.add(path1)
            
            for path2, hash2 in phashes.items():
                if path2 in processed:
                    continue
                
                # Calculate Hamming distance
                distance = hash1 - hash2
                
                if distance <= self.similarity_threshold:
                    group.append(path2)
                    processed.add(path2)
            
            if len(group) > 1:
                similar_groups.append(group)
        
        # Create DuplicateGroup objects
        groups = []
        for idx, file_list in enumerate(similar_groups):
            group = DuplicateGroup(
                group_id=f"similar_{idx}",
                duplicate_type=DuplicateType.SIMILAR,
                files=file_list
            )
            groups.append(group)
        
        return groups
    
    def _compute_file_hash(self, file_path: Path) -> Optional[str]:
        """Compute hash of file contents."""
        # Check cache
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]
        
        try:
            hasher = hashlib.new(self.hash_algorithm)
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    hasher.update(chunk)
            
            file_hash = hasher.hexdigest()
            self._hash_cache[file_path] = file_hash
            return file_hash
            
        except Exception as e:
            self.logger.warning(f"Failed to hash {file_path}: {e}")
            return None
    
    def _compute_perceptual_hash(self, image_path: Path) -> Optional[Any]:
        """Compute perceptual hash of an image."""
        # Check cache
        if image_path in self._perceptual_hash_cache:
            from imagehash import hex_to_hash
            return hex_to_hash(self._perceptual_hash_cache[image_path])
        
        try:
            from PIL import Image
            import imagehash
            
            with Image.open(image_path) as img:
                # Use phash (perceptual hash) by default
                phash = imagehash.phash(img)
                self._perceptual_hash_cache[image_path] = str(phash)
                return phash
                
        except Exception as e:
            self.logger.debug(f"Failed to compute perceptual hash for {image_path}: {e}")
            return None
    
    def quick_check_duplicates(self, file_path: Union[str, Path],
                               other_paths: List[Union[str, Path]]) -> List[Path]:
        """
        Quick check if a file is a duplicate of any in a list.
        
        Args:
            file_path: File to check
            other_paths: List of files to compare against
            
        Returns:
            List of paths that are duplicates
        """
        file_path = Path(file_path)
        other_paths = [Path(p) for p in other_paths]
        
        file_hash = self._compute_file_hash(file_path)
        if not file_hash:
            return []
        
        duplicates = []
        for other_path in other_paths:
            other_hash = self._compute_file_hash(other_path)
            if other_hash == file_hash:
                duplicates.append(other_path)
        
        return duplicates
    
    def delete_duplicates(self, 
                         group: DuplicateGroup,
                         keep_indices: List[int],
                         dry_run: bool = True) -> Dict[str, any]:
        """
        Delete duplicate files, keeping specified ones.
        
        Args:
            group: Duplicate group
            keep_indices: Indices of files to keep
            dry_run: If True, only simulate deletion
            
        Returns:
            Dict with deletion results
        """
        if not group.files:
            return {'deleted': [], 'errors': [], 'space_freed': 0}
        
        deleted = []
        errors = []
        space_freed = 0
        
        for i, file_path in enumerate(group.files):
            if i in keep_indices:
                continue  # Keep this file
            
            try:
                if not dry_run:
                    file_size = file_path.stat().st_size
                    file_path.unlink()
                    space_freed += file_size
                else:
                    space_freed += file_path.stat().st_size
                
                deleted.append(file_path)
                self.logger.info(f"{'Would delete' if dry_run else 'Deleted'}: {file_path}")
                
            except Exception as e:
                errors.append(f"{file_path}: {e}")
                self.logger.error(f"Failed to delete {file_path}: {e}")
        
        return {
            'deleted': deleted,
            'errors': errors,
            'space_freed': space_freed,
            'dry_run': dry_run
        }
    
    def delete_all_but_one(self,
                          group: DuplicateGroup,
                          keep_index: int = 0,
                          dry_run: bool = True) -> Dict[str, any]:
        """
        Delete all duplicates except one.
        
        Args:
            group: Duplicate group
            keep_index: Index of file to keep (default: first)
            dry_run: If True, only simulate deletion
            
        Returns:
            Dict with deletion results
        """
        keep_indices = [keep_index] if keep_index < len(group.files) else [0]
        return self.delete_duplicates(group, keep_indices, dry_run)
    
    def clear_cache(self) -> None:
        """Clear hash caches."""
        self._hash_cache.clear()
        self._perceptual_hash_cache.clear()
        self.logger.debug("Hash cache cleared")
    
    def get_file_hash(self, file_path: Union[str, Path]) -> Optional[str]:
        """Get hash for a file (computes if not cached)."""
        return self._compute_file_hash(Path(file_path))
    
    def compare_files(self, file1: Union[str, Path], 
                     file2: Union[str, Path]) -> Dict[str, any]:
        """
        Compare two files for similarity.
        
        Args:
            file1: First file path
            file2: Second file path
            
        Returns:
            Dict with comparison results
        """
        file1 = Path(file1)
        file2 = Path(file2)
        
        result = {
            'identical': False,
            'same_size': False,
            'size_difference': 0,
            'hash1': None,
            'hash2': None,
            'similarity': None
        }
        
        try:
            stat1 = file1.stat()
            stat2 = file2.stat()
            
            result['same_size'] = stat1.st_size == stat2.st_size
            result['size_difference'] = abs(stat1.st_size - stat2.st_size)
            
            # Compute hashes
            hash1 = self._compute_file_hash(file1)
            hash2 = self._compute_file_hash(file2)
            
            result['hash1'] = hash1
            result['hash2'] = hash2
            result['identical'] = hash1 == hash2 and hash1 is not None
            
            # Check perceptual similarity for images
            if (file1.suffix.lower() in self.IMAGE_EXTENSIONS and 
                file2.suffix.lower() in self.IMAGE_EXTENSIONS):
                try:
                    phash1 = self._compute_perceptual_hash(file1)
                    phash2 = self._compute_perceptual_hash(file2)
                    
                    if phash1 and phash2:
                        result['similarity'] = phash1 - phash2
                except:
                    pass
                    
        except Exception as e:
            result['error'] = str(e)
        
        return result
