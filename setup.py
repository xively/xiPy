from setuptools import setup

setup(name='xiPy',
	version='1.0.0rc1',
	description="Xively Client Python Library",
	long_description="The official pythonic library for the next-gen Xively platform.",
	url='http://github.com/xively/xiPy',
	author='Xively by LogMeIn, Inc.',
	author_email='XivelyInfo@LogMeIn.com',
	license='BSD 3-Clause',
	packages=['xiPy'],
	install_requires=[ ],
	package_data={
		'xiPy' : [
			'certs/GeoTrust Primary Certification Authority - G3.pem',
			'certs/GlobalSign Root CA.pem',
			'certs/thawte Primary Root CA - G3.pem',
			'certs/VeriSign Class 3 Public Primary Certification Authority - G5.pem',
			'licenses/edl-v10',
			'licenses/epl-v10',
			'licenses/LICENSE.md',
			'licenses/PAHO-MQTT-PYTHON-LICENSE.txt'
		]
	},
	classifiers=[
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: 3.4',
		'Programming Language :: Python :: 3.5'
	],
	zip_safe=True)
