# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    unzip \
    default-jdk \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set JAVA_HOME environment variable
ENV JAVA_HOME=/usr/lib/jvm/default-java
ENV PATH=$PATH:$JAVA_HOME/bin

# Download and install PMD including rulesets
ENV PMD_VERSION=7.15.0
RUN curl -L -o pmd.zip https://github.com/pmd/pmd/releases/download/pmd_releases%2F${PMD_VERSION}/pmd-dist-${PMD_VERSION}-bin.zip \
    && unzip pmd.zip -d /opt \
    && rm pmd.zip



# Set PMD path
ENV PMD_HOME=/opt/pmd-bin-${PMD_VERSION}
ENV PATH="$PMD_HOME/bin:$PATH"

# clone the remote git repository with analysis code 
RUN git clone https://github.com/Lbyrigitte/pmd-analysis.git /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
#COPY *.py ./
#COPY *.xml ./

# Create output directory
RUN mkdir -p /app/output

# Set default command with PMD path
ENTRYPOINT ["python", "main.py"]
CMD ["--help"]
