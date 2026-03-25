from setuptools import setup, find_packages

setup(
    name="ab_testing_project",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Production-grade A/B testing framework for e-commerce checkout optimization",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ab-testing-project",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "pandas>=2.1.0",
        "numpy>=1.26.0",
        "scipy>=1.11.0",
        "statsmodels>=0.14.0",
        "matplotlib>=3.8.0",
        "seaborn>=0.13.0",
    ],
    extras_require={
        "bayesian": ["pymc>=5.10.0", "arviz>=0.17.0"],
        "dev": ["pytest>=7.4.0", "pytest-cov>=4.1.0", "jupyterlab>=4.0.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)
