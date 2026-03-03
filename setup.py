from setuptools import setup, find_packages

setup(
    name='gesture-ui-control',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        # Add any necessary dependencies here
    ],
    entry_points={
        'console_scripts': [
            'gesture-control=gesture_control:main',
        ],
    },
    author='Shikhar7263',
    author_email='your-email@example.com',
    description='A gesture control system for UI interaction',
    url='https://github.com/Shikhar7263/gesture-ui-control',
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.6',
)