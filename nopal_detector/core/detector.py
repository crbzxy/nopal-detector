"""
Detector principal de nopal que orqueste todos los servicios.
"""

from typing import Optional, Tuple, Any

from ..config.settings import ApplicationConfig
from ..services.detection import OpenCVService
from ..services.color_detection import ColorDetectionService, ColorDetectionConfig, create_default_color_config
from ..services.sources import SourceManager
from ..services.output import OutputManager, OutputFactory
from ..utils.logging import setup_logger


class NopalDetector:
    """Detector principal de nopal que orqueste todos los componentes."""
    
    def __init__(self, config: ApplicationConfig):
        self.config = config
        self.logger = setup_logger(__name__)
        
        # Inicializar servicios
        self.opencv_service = OpenCVService(
            orb_config=config.orb,
            drawing_config=config.drawing
        )
        
        # Servicio de detección por color
        color_config = ColorDetectionConfig(
            hsv_ranges=config.color_detection.hsv_ranges,
            min_area=config.color_detection.min_area,
            max_area=config.color_detection.max_area,
            aspect_min=config.color_detection.aspect_min,
            aspect_max=config.color_detection.aspect_max,
            solidity_min=config.color_detection.solidity_min,
            blur_kernel_size=config.color_detection.blur_kernel_size,
            morph_kernel_size=config.color_detection.morph_kernel_size,
            draw_border=(0, 0, 0),  # Negro por defecto
            draw_fill=config.drawing.fill_color,
            fill_alpha=config.drawing.fill_alpha,
            draw_bbox=config.color_detection.draw_bbox,
            draw_labels=config.color_detection.draw_labels
        )
        self.color_service = ColorDetectionService(color_config)
        
        self.output_manager = OutputManager()
    
    def detect_from_source(
        self,
        source_path: str,
        reference_path: str,
        output_path: Optional[str] = None,
        mask_path: Optional[str] = None,
        show_display: bool = True,
        detector_mode: str = "auto",
        custom_orb_params: Optional[dict] = None,
        custom_drawing_params: Optional[dict] = None,
        custom_color_params: Optional[dict] = None
    ) -> bool:
        """
        Ejecuta detección desde una fuente de entrada.
        
        Args:
            source_path: Ruta de la fuente (imagen, video, o índice de cámara)
            reference_path: Ruta de la imagen de referencia
            output_path: Ruta para guardar resultado (opcional)
            mask_path: Ruta para guardar máscara (opcional)
            show_display: Si mostrar ventana de visualización
            detector_mode: Modo de detección ("orb", "color", "auto")
            custom_orb_params: Parámetros ORB personalizados
            custom_drawing_params: Parámetros de dibujo personalizados
            custom_color_params: Parámetros de detección por color personalizados
            
        Returns:
            True si la operación fue exitosa
        """
        try:
            # Aplicar parámetros personalizados si se proporcionan
            self._apply_custom_params(custom_orb_params, custom_drawing_params, custom_color_params)
            
            # Cargar imagen de referencia solo si se va a usar ORB
            if detector_mode in ["orb", "auto"]:
                self.logger.info(f"Cargando referencia: {reference_path}")
                self.opencv_service.load_reference(reference_path)
            
            # Configurar observadores de output
            self._setup_output_observers(
                source_path, output_path, mask_path, show_display
            )
            
            # Procesar según el tipo de fuente
            success = self._process_source(source_path, detector_mode)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error en detección: {e}")
            return False
        finally:
            # Limpiar recursos
            self.output_manager.cleanup()
    
    def _apply_custom_params(
        self, 
        custom_orb_params: Optional[dict], 
        custom_drawing_params: Optional[dict],
        custom_color_params: Optional[dict]
    ) -> None:
        """Aplica parámetros personalizados a la configuración."""
        if custom_orb_params:
            for key, value in custom_orb_params.items():
                if hasattr(self.config.orb, key):
                    setattr(self.config.orb, key, value)
                    self.logger.info(f"ORB param actualizado: {key}={value}")
        
        if custom_drawing_params:
            for key, value in custom_drawing_params.items():
                if hasattr(self.config.drawing, key):
                    setattr(self.config.drawing, key, value)
                    self.logger.info(f"Drawing param actualizado: {key}={value}")
        
        if custom_color_params:
            for key, value in custom_color_params.items():
                if hasattr(self.config.color_detection, key):
                    setattr(self.config.color_detection, key, value)
                    # Actualizar también el servicio de color
                    if hasattr(self.color_service.config, key):
                        setattr(self.color_service.config, key, value)
                    self.logger.info(f"Color param actualizado: {key}={value}")
    
    def _setup_output_observers(
        self,
        source_path: str,
        output_path: Optional[str],
        mask_path: Optional[str],
        show_display: bool
    ) -> None:
        """Configura los observadores de output según los parámetros."""
        
        # Determinar tipo de fuente para configurar observers apropiados
        with SourceManager(source_path) as source_manager:
            source_type = source_manager.get_source_type()
            
            # Observer de display
            if show_display:
                display_observer = OutputFactory.create_display_observer()
                self.output_manager.add_observer(display_observer)
            
            # Observer de guardado principal
            if output_path:
                video_config = None
                if source_manager.is_stream:
                    try:
                        width, height, fps = source_manager.get_video_properties()
                        video_config = {
                            'fourcc': self.config.video.fourcc,
                            'fps': fps
                        }
                    except ValueError:
                        # No es un stream válido, usar configuración por defecto
                        video_config = {
                            'fourcc': self.config.video.fourcc,
                            'fps': self.config.video.default_fps
                        }
                
                save_observer = OutputFactory.create_save_observer(
                    output_path, source_type, video_config
                )
                self.output_manager.add_observer(save_observer)
            
            # Observer de máscara (solo para imágenes)
            if mask_path and source_type == "image":
                mask_observer = OutputFactory.create_mask_observer(mask_path)
                self.output_manager.add_observer(mask_observer)
    
    def _process_source(self, source_path: str, detector_mode: str) -> bool:
        """
        Procesa la fuente de entrada.
        
        Args:
            source_path: Ruta de la fuente
            detector_mode: Modo de detección ("orb", "color", "auto")
            
        Returns:
            True si el procesamiento fue exitoso
        """
        try:
            with SourceManager(source_path) as source_manager:
                source_type = source_manager.get_source_type()
                self.logger.info(f"Procesando fuente tipo: {source_type} con detector: {detector_mode}")
                
                if source_manager.is_stream:
                    return self._process_stream(source_manager, detector_mode)
                else:
                    return self._process_single_frame(source_manager, detector_mode)
                    
        except Exception as e:
            self.logger.error(f"Error procesando fuente: {e}")
            return False
    
    def _process_stream(self, source_manager: SourceManager, detector_mode: str) -> bool:
        """
        Procesa un stream (video o cámara).
        
        Args:
            source_manager: Manager de la fuente
            detector_mode: Modo de detección
            
        Returns:
            True si el procesamiento fue exitoso
        """
        frame_count = 0
        detection_count = 0
        
        self.logger.info("Iniciando procesamiento de stream (presiona 'q' para salir)")
        
        while True:
            frame = source_manager.read_frame()
            if frame is None:
                self.logger.info("Fin del stream")
                break
            
            frame_count += 1
            
            # Detectar en el frame según el modo
            result_frame, result_mask, has_detection, matches_or_detections = self._detect_with_mode(
                frame, detector_mode
            )
            
            if has_detection:
                detection_count += 1
            
            # Crear metadata
            metadata = {
                'is_stream': True,
                'source_type': source_manager.get_source_type(),
                'frame_number': frame_count,
                'matches': matches_or_detections,
                'has_detection': has_detection,
                'should_exit': False
            }
            
            # Notificar a observers
            self.output_manager.notify_result(
                result_frame, 
                result_mask, 
                metadata
            )
            
            # Verificar si se debe salir
            if metadata.get('should_exit', False):
                break
        
        self.logger.info(
            f"Stream procesado: {frame_count} frames, "
            f"{detection_count} detecciones"
        )
        
        return True
    
    def _process_single_frame(self, source_manager: SourceManager, detector_mode: str) -> bool:
        """
        Procesa una imagen individual.
        
        Args:
            source_manager: Manager de la fuente
            detector_mode: Modo de detección
            
        Returns:
            True si el procesamiento fue exitoso
        """
        frame = source_manager.current_frame
        if frame is None:
            self.logger.error("No se pudo obtener el frame")
            return False
        
        self.logger.info("Procesando imagen")
        
        # Detectar según el modo
        result_frame, result_mask, has_detection, matches_or_detections = self._detect_with_mode(
            frame, detector_mode
        )
        
        # Crear metadata
        metadata = {
            'is_stream': False,
            'source_type': source_manager.get_source_type(),
            'matches': matches_or_detections,
            'has_detection': has_detection
        }
        
        # Notificar a observers
        self.output_manager.notify_result(
            result_frame, 
            result_mask, 
            metadata
        )
        
        if has_detection:
            if detector_mode == "color":
                self.logger.info(f"¡Nopal detectado por color! ({matches_or_detections} objetos)")
            else:
                self.logger.info(f"¡Nopal detectado! ({matches_or_detections} matches)")
        else:
            if detector_mode == "color":
                self.logger.info("No se detectaron objetos por color")
            else:
                self.logger.info(f"No se detectó nopal ({matches_or_detections} matches)")
        
        return True
    
    def _detect_with_mode(self, frame: Any, detector_mode: str) -> Tuple[Any, Optional[Any], bool, int]:
        """
        Detecta usando el modo especificado (ORB, COLOR, o AUTO).
        
        Args:
            frame: Frame de entrada
            detector_mode: "orb", "color", o "auto"
            
        Returns:
            Tupla (frame_procesado, mask, has_detection, matches_o_detecciones)
        """
        if detector_mode == "orb":
            # Solo ORB
            result = self.opencv_service.detect_in_frame(frame)
            return result.frame_with_overlay, result.mask, result.has_detection, result.matches_found
        
        elif detector_mode == "color":
            # Solo color
            result = self.color_service.detect_in_frame(frame)
            return result.frame_with_overlay, result.mask, result.total_detections > 0, result.total_detections
        
        elif detector_mode == "auto":
            # AUTO: Intentar ORB primero, si falla usar COLOR
            orb_result = self.opencv_service.detect_in_frame(frame)
            
            if orb_result.has_detection:
                # ORB tuvo éxito
                self.logger.debug(f"ORB exitoso: {orb_result.matches_found} matches")
                return orb_result.frame_with_overlay, orb_result.mask, True, orb_result.matches_found
            else:
                # ORB falló, intentar COLOR como fallback
                self.logger.debug(f"ORB falló ({orb_result.matches_found} matches), intentando color...")
                color_result = self.color_service.detect_in_frame(frame)
                
                if color_result.total_detections > 0:
                    self.logger.info(f"Fallback a color exitoso: {color_result.total_detections} objetos")
                    return color_result.frame_with_overlay, color_result.mask, True, color_result.total_detections
                else:
                    # Ninguno tuvo éxito, devolver resultado ORB original
                    self.logger.debug("Tanto ORB como COLOR fallaron")
                    return orb_result.frame_with_overlay, orb_result.mask, False, orb_result.matches_found
        
        else:
            # Modo inválido, usar ORB por defecto
            self.logger.warning(f"Modo de detector inválido: {detector_mode}, usando ORB")
            result = self.opencv_service.detect_in_frame(frame)
            return result.frame_with_overlay, result.mask, result.has_detection, result.matches_found
    
    def get_detection_stats(self) -> dict:
        """
        Obtiene estadísticas de detección.
        
        Returns:
            Diccionario con estadísticas
        """
        # Por ahora retorna información básica de configuración
        return {
            'orb_features': self.config.orb.n_features,
            'min_matches': self.config.orb.min_matches,
            'ratio_threshold': self.config.orb.ratio_threshold,
            'has_reference': self.opencv_service._reference_data is not None
        }