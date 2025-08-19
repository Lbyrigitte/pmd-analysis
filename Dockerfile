# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies including openjdk
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    git \
    wget \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH="$JAVA_HOME/bin:$PATH"

# Download and install PMD including rulesets
ENV PMD_VERSION=7.15.0
RUN curl -L -o pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F${PMD_VERSION}/pmd-dist-${PMD_VERSION}-bin.zip \
    && unzip pmd.zip -d /opt \
    && rm pmd.zip


# Set PMD permissions and path
#RUN chmod +x /app/pmd/pmd-bin-7.15.0/bin/pmd && \
    #chmod +x /app/pmd/pmd-bin-7.15.0/bin/pmd.bat

# Set PMD path
ENV PMD_HOME=/opt/pmd-bin-${PMD_VERSION}
ENV PATH="$PMD_HOME/bin:$PATH"

# clone  my github 
RUN git clone https://github.com/Lbyrigitte/pmd-analysis.git /app


# Install Python dependencies
RUN pip install --no-cache-dir \
    GitPython==3.1.40 \
    requests==2.31.0 \
    click==8.1.7 \
    tqdm==4.66.1 \
    python-dateutil==2.8.2


# Create output directory
RUN mkdir -p /app/output

# Set default command with PMD path
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]