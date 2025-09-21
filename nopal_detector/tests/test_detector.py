"""
Ejemplo de tests para mostrar la testabilidad de la nueva arquitectura.

Para ejecutar: python -m pytest nopal_detector/tests/
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path

from ..config.settings import ApplicationConfig, ORBConfig, DrawingConfig
from ..core.detector import NopalDetector
from ..services.detection import OpenCVService, DetectionResult


class TestApplicationConfig:
    """Tests para la configuración de la aplicación."""
    
    def test_create_default_config(self):
        """Test que verifica la creación de configuración por defecto."""
        config = ApplicationConfig.create_default()
        
        assert config is not None
        assert config.orb.min_matches == 18
        assert config.orb.ratio_threshold == 0.75
        assert config.drawing.fill_alpha == 0.25
        assert config.default_ref_path == "data/ref/nopal_ref.jpg"
    
    def test_orb_config_validation(self):
        """Test que verifica la validación de configuración ORB."""
        orb_config = ORBConfig(
            min_matches=10,
            ratio_threshold=0.8,
            n_features=1000
        )
        
        assert orb_config.min_matches == 10
        assert orb_config.ratio_threshold == 0.8
        assert orb_config.n_features == 1000
    
    def test_drawing_config_colors(self):
        """Test que verifica la configuración de colores."""
        drawing_config = DrawingConfig(
            border_color=(255, 0, 0),  # Rojo
            fill_color=(0, 255, 0),    # Verde
            fill_alpha=0.5
        )
        
        assert drawing_config.border_color == (255, 0, 0)
        assert drawing_config.fill_color == (0, 255, 0)
        assert drawing_config.fill_alpha == 0.5


class TestNopalDetector:
    """Tests para el detector principal."""
    
    def test_detector_initialization(self):
        """Test que verifica la inicialización del detector."""
        config = ApplicationConfig.create_default()
        detector = NopalDetector(config)
        
        assert detector.config is config
        assert detector.opencv_service is not None
        assert detector.output_manager is not None
    
    def test_detector_stats(self):
        """Test que verifica las estadísticas del detector."""
        config = ApplicationConfig.create_default()
        detector = NopalDetector(config)
        
        stats = detector.get_detection_stats()
        
        assert 'orb_features' in stats
        assert 'min_matches' in stats
        assert 'ratio_threshold' in stats
        assert 'has_reference' in stats
        assert stats['orb_features'] == 2000
        assert stats['min_matches'] == 18
    
    @patch('nopal_detector.services.sources.SourceManager')
    @patch('nopal_detector.services.detection.OpenCVService')
    def test_apply_custom_params(self, mock_opencv, mock_source):
        """Test que verifica la aplicación de parámetros personalizados."""
        config = ApplicationConfig.create_default()
        detector = NopalDetector(config)
        
        custom_orb = {'min_matches': 25, 'ratio_threshold': 0.8}
        custom_drawing = {'fill_alpha': 0.4}
        
        # Simular métodos necesarios
        detector._apply_custom_params(custom_orb, custom_drawing)
        
        assert config.orb.min_matches == 25
        assert config.orb.ratio_threshold == 0.8
        assert config.drawing.fill_alpha == 0.4


class TestOpenCVService:
    """Tests para el servicio OpenCV."""
    
    def test_opencv_service_initialization(self):
        """Test que verifica la inicialización del servicio OpenCV."""
        orb_config = ORBConfig()
        drawing_config = DrawingConfig()
        
        service = OpenCVService(orb_config, drawing_config)
        
        assert service.orb_config is orb_config
        assert service.drawing_config is drawing_config
        assert service._orb is None  # Lazy loading
        assert service._reference_data is None
    
    def test_detection_result_structure(self):
        """Test que verifica la estructura del resultado de detección."""
        # Crear un resultado mock
        fake_frame = "fake_frame_data"
        fake_mask = "fake_mask_data"
        
        result = DetectionResult(
            frame_with_overlay=fake_frame,
            mask=fake_mask,
            matches_found=15,
            has_detection=False
        )
        
        assert result.frame_with_overlay == fake_frame
        assert result.mask == fake_mask
        assert result.matches_found == 15
        assert result.has_detection is False
        assert result.homography is None  # Default value


@pytest.fixture
def temp_config():
    """Fixture que proporciona una configuración temporal para tests."""
    return ApplicationConfig.create_default()


@pytest.fixture
def mock_opencv_service():
    """Fixture que proporciona un servicio OpenCV mockeado."""
    mock_service = Mock(spec=OpenCVService)
    mock_service.load_reference.return_value = None
    mock_service.detect_in_frame.return_value = DetectionResult(
        frame_with_overlay="processed_frame",
        mask=None,
        matches_found=10,
        has_detection=False
    )
    return mock_service


class TestIntegration:
    """Tests de integración que verifican la interacción entre componentes."""
    
    def test_detector_with_mock_opencv(self, temp_config, mock_opencv_service):
        """Test de integración usando mocks."""
        detector = NopalDetector(temp_config)
        detector.opencv_service = mock_opencv_service
        
        # Verificar que se pueden obtener estadísticas
        stats = detector.get_detection_stats()
        assert isinstance(stats, dict)
        
        # Verificar que el servicio está configurado
        assert detector.opencv_service is mock_opencv_service


# Ejemplo de cómo se ejecutarían los tests:
if __name__ == "__main__":
    # python -m pytest nopal_detector/tests/test_detector.py -v
    pytest.main([__file__, "-v"])