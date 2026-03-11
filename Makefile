.PHONY: discover test run analyze unknot mesh gui gui-offscreen test-gui run-all clean

discover:
	.\\.venv\\Scripts\\python.exe scripts\\discover_apis.py

test:
	.\\.venv\\Scripts\\python.exe -m pytest -v tests

analyze:
	.\\.venv\\Scripts\\python.exe main.py --pd-file examples\\reference_11c.json --analyze --out out\\reference

unknot:
	.\\.venv\\Scripts\\python.exe main.py --pd-file examples\\trefoil.json --unknotting-search --out out\\trefoil

mesh:
	.\\.venv\\Scripts\\python.exe main.py --pd-file examples\\trefoil.json --analyze --export-mesh --out out\\trefoil_mesh

gui:
	.\\.venv\\Scripts\\python.exe gui_main.py

gui-offscreen:
	powershell -Command "$$env:QT_QPA_PLATFORM='offscreen'; $$env:PYVISTA_OFF_SCREEN='true'; .\\.venv\\Scripts\\python.exe gui_main.py"

test-gui:
	powershell -Command "$$env:QT_QPA_PLATFORM='offscreen'; $$env:PYVISTA_OFF_SCREEN='true'; .\\.venv\\Scripts\\python.exe -m pytest -v tests\\test_main_window.py tests\\test_gui_integration.py"

run-all:
	.\\.venv\\Scripts\\python.exe examples\\run_all.py

clean:
	powershell -Command "Remove-Item -Force -Recurse out\\* -ErrorAction SilentlyContinue"
