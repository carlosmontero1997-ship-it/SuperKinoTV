import sys
import os

# Añadir el directorio padre del directorio 'superkino' al path
# Así 'core' será importable desde los tests
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))