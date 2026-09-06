.PHONY: build check calibrate clean all

all: build check calibrate

build:
	@for d in 0*/; do echo "== $$d"; (cd $$d && python3 build.py); done

check:
	python3 tools/validate_k.py 0*/models/*.k
	python3 tools/mesh_quality.py 0*/models/*.k

calibrate:
	cd 02_gissmo_calibration && python3 calibrate.py
	cd 04_spotweld_coupons && python3 calibrate.py

clean:
	rm -rf 0*/models/*.k 0*/results __pycache__ tools/__pycache__
