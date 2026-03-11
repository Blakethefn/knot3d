.PHONY: discover test run analyze unknot mesh run-all clean

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

run-all:
	.\\.venv\\Scripts\\python.exe examples\\run_all.py

clean:
	powershell -Command "Remove-Item -Force -Recurse out\\* -ErrorAction SilentlyContinue"
