
.PHONY: install publish test

install:
	python setup.py install

publish:
	python setup.py sdist upload -r pypi

testpublish:
	python setup.py sdist upload -r pypitest

test:
	nosetests
