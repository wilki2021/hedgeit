default: clean test

clean:
	find . -name "*.pyc" | xargs rm -f

test:
	python -m unittest discover hedgeit/test/ '*.py' hedgeit/test/

