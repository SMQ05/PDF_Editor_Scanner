"""
Domain Models for PDF Scanner App.
Data classes representing core entities.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class FilterType(Enum):
    """Available image filters for scanned pages."""
    ORIGINAL = "original"
    GRAYSCALE = "grayscale"
    BLACK_WHITE = "black_white"
    ENHANCED = "enhanced"


class CompressionPreset(Enum):
    """PDF compression presets."""
    SMALL = "small"       # max 1600px, JPEG q=50
    BALANCED = "balanced" # max 2000px, JPEG q=65
    HIGH = "high"         # max 2500px, JPEG q=80
    
    @property
    def max_dimension(self) -> int:
        """Get max dimension for this preset."""
        return {
            CompressionPreset.SMALL: 1600,
            CompressionPreset.BALANCED: 2000,
            CompressionPreset.HIGH: 2500,
        }[self]
    
    @property
    def jpeg_quality(self) -> int:
        """Get JPEG quality for this preset."""
        return {
            CompressionPreset.SMALL: 50,
            CompressionPreset.BALANCED: 65,
            CompressionPreset.HIGH: 80,
        }[self]


@dataclass
class Page:
    """Represents a single scanned page."""
    id: Optional[int] = None
    document_id: Optional[int] = None
    order: int = 0
    image_path: str = ""
    thumbnail_path: str = ""
    filter_applied: FilterType = FilterType.ORIGINAL
    quad_points: Optional[List[tuple]] = None  # [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
    rotation: int = 0  # 0, 90, 180, 270
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'order': self.order,
            'image_path': self.image_path,
            'thumbnail_path': self.thumbnail_path,
            'filter_applied': self.filter_applied.value,
            'quad_points': str(self.quad_points) if self.quad_points else None,
            'rotation': self.rotation,
            'created_at': self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Page':
        """Create from dictionary."""
        quad_points = None
        if data.get('quad_points'):
            try:
                quad_points = eval(data['quad_points'])
            except:
                pass
        return cls(
            id=data.get('id'),
            document_id=data.get('document_id'),
            order=data.get('order', 0),
            image_path=data.get('image_path', ''),
            thumbnail_path=data.get('thumbnail_path', ''),
            filter_applied=FilterType(data.get('filter_applied', 'original')),
            quad_points=quad_points,
            rotation=data.get('rotation', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
        )


@dataclass
class Document:
    """Represents a PDF document."""
    id: Optional[int] = None
    name: str = "Untitled"
    file_path: str = ""
    thumbnail_path: str = ""
    page_count: int = 0
    file_size: int = 0  # bytes
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'name': self.name,
            'file_path': self.file_path,
            'thumbnail_path': self.thumbnail_path,
            'page_count': self.page_count,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Document':
        """Create from dictionary."""
        return cls(
            id=data.get('id'),
            name=data.get('name', 'Untitled'),
            file_path=data.get('file_path', ''),
            thumbnail_path=data.get('thumbnail_path', ''),
            page_count=data.get('page_count', 0),
            file_size=data.get('file_size', 0),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else datetime.now(),
        )


@dataclass
class ScanSession:
    """Represents an ongoing scan session (for persistence across process death)."""
    id: Optional[int] = None
    pages: List[Page] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    is_complete: bool = False
    current_page_index: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'id': self.id,
            'pages': [p.to_dict() for p in self.pages],
            'started_at': self.started_at.isoformat(),
            'is_complete': self.is_complete,
            'current_page_index': self.current_page_index,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScanSession':
        """Create from dictionary."""
        pages = [Page.from_dict(p) for p in data.get('pages', [])]
        return cls(
            id=data.get('id'),
            pages=pages,
            started_at=datetime.fromisoformat(data['started_at']) if data.get('started_at') else datetime.now(),
            is_complete=data.get('is_complete', False),
            current_page_index=data.get('current_page_index', 0),
        )
    
    def add_page(self, page: Page):
        """Add a page to the session."""
        page.order = len(self.pages)
        self.pages.append(page)
        self.current_page_index = len(self.pages) - 1
    
    def remove_page(self, index: int):
        """Remove a page by index."""
        if 0 <= index < len(self.pages):
            self.pages.pop(index)
            # Reorder remaining pages
            for i, page in enumerate(self.pages):
                page.order = i
    
    def reorder_pages(self, from_index: int, to_index: int):
        """Move a page from one position to another."""
        if 0 <= from_index < len(self.pages) and 0 <= to_index < len(self.pages):
            page = self.pages.pop(from_index)
            self.pages.insert(to_index, page)
            # Update order values
            for i, p in enumerate(self.pages):
                p.order = i


@dataclass
class AppState:
    """Application state for ads and purchases."""
    ads_enabled: bool = True
    ads_removed_purchased: bool = False
    last_interstitial_time: Optional[datetime] = None
    interstitial_count_today: int = 0
    last_count_reset_date: Optional[str] = None  # YYYY-MM-DD
    max_pages_per_document: int = 200
    
    # Frequency cap settings
    MIN_INTERSTITIAL_INTERVAL_SECONDS: int = 30
    MAX_INTERSTITIALS_PER_DAY: int = 20
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            'ads_enabled': self.ads_enabled,
            'ads_removed_purchased': self.ads_removed_purchased,
            'last_interstitial_time': self.last_interstitial_time.isoformat() if self.last_interstitial_time else None,
            'interstitial_count_today': self.interstitial_count_today,
            'last_count_reset_date': self.last_count_reset_date,
            'max_pages_per_document': self.max_pages_per_document,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AppState':
        """Create from dictionary."""
        last_time = None
        if data.get('last_interstitial_time'):
            try:
                last_time = datetime.fromisoformat(data['last_interstitial_time'])
            except:
                pass
        return cls(
            ads_enabled=data.get('ads_enabled', True),
            ads_removed_purchased=data.get('ads_removed_purchased', False),
            last_interstitial_time=last_time,
            interstitial_count_today=data.get('interstitial_count_today', 0),
            last_count_reset_date=data.get('last_count_reset_date'),
            max_pages_per_document=data.get('max_pages_per_document', 200),
        )
    
    def can_show_interstitial(self) -> bool:
        """Check if an interstitial ad can be shown based on frequency cap."""
        if not self.ads_enabled or self.ads_removed_purchased:
            return False
        
        # Reset daily count if needed
        today = datetime.now().strftime('%Y-%m-%d')
        if self.last_count_reset_date != today:
            self.interstitial_count_today = 0
            self.last_count_reset_date = today
        
        # Check daily limit
        if self.interstitial_count_today >= self.MAX_INTERSTITIALS_PER_DAY:
            return False
        
        # Check time interval
        if self.last_interstitial_time:
            elapsed = (datetime.now() - self.last_interstitial_time).total_seconds()
            if elapsed < self.MIN_INTERSTITIAL_INTERVAL_SECONDS:
                return False
        
        return True
    
    def record_interstitial_shown(self):
        """Record that an interstitial was shown."""
        self.last_interstitial_time = datetime.now()
        self.interstitial_count_today += 1


@dataclass
class QuadResult:
    """Result of document edge detection."""
    detected: bool = False
    points: Optional[List[tuple]] = None  # [(x1,y1), (x2,y2), (x3,y3), (x4,y4)] in clockwise order
    confidence: float = 0.0
    frame_size: tuple = (0, 0)  # (width, height) of the analyzed frame
    
    @property
    def is_valid(self) -> bool:
        """Check if detected quad is valid."""
        return self.detected and self.points is not None and len(self.points) == 4


@dataclass
class ProcessingResult:
    """Result of image processing operation."""
    success: bool = False
    output_path: str = ""
    error_message: str = ""
    processing_time_ms: int = 0
