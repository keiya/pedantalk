.PHONY: setup install lint type-check format run clean

setup:
	python -m venv venv
	@echo "Virtual environment created. Run 'source venv/bin/activate' to activate it."

install:
	pip install -r requirements.txt

lint:
	pylint pedantalk
	flake8 pedantalk

type-check:
	mypy pedantalk

format:
	black pedantalk
	isort pedantalk

run:
	python -m pedantalk.main

clean:
	rm -rf output/audio/*
	rm -rf output/transcripts/*
	rm -f output/pedantalk.log

all: install lint type-check format 
