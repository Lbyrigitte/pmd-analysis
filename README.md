# Repository Mining and Analysis by PMD

## Overview

This project provides a [Docker-based program](https://www.docker.com/) that performs static analysis on each commit of a selected Java Git repository using [PMD](https://pmd.github.io/). It is designed for **software repository mining** and generates detailed analysis results per commit, along with a final summary report.


## Core Functionalities
- Support for local and remote Git repositories
- Dockerized execution
- Commit-by-commit traversal of the full Git history
- PMD static analysis performed on each revision
- Per-commit JSON reports with detailed findings
- Summary report generation including commit count, average number of Java files, average warnings, and types of warnings
- Configurable input/output paths and rulesets for flexible setup


## Update
```
example-ruleset.xml
minimal-ruleset.xml
simple-ruleset.xml
ultra-minimal-ruleset.xml

DOCKER_USAGE.md
LOCAL_USAGE.md- Remove unnecessary/redundant files
PMD_PATH_CONFIG.md

docker-compose.yml

./output
./pmd/pmd-dist-7.15.0-bin/pmd-bin-7.15.0

Dockerfile
summary_generator.py
```

## Project Structure
 (project-root)**pmd_miner**/    
├──output    
│     ├──commits #Detailed json file    
│     ├──logs    
│     └──summary.json #summary file    
├── main.py # Main program entry    
├── git_analyzer.py # Git repository analysis module    
├── pmd_runner.py # PMD execution module    
├── result_processor.py # Result processing module    
├── summary_generator.py # Summary generation module    
├── requirements.txt # Python dependencies    
├── Dockerfile # Docker image definition    
├── test_performance_display.py # est the performance display effect of different submission numbers    
└── README.md         # This file    
 
## Usage Instructions or Examples

Will be detailed in the section below.


##  Installation & Execution

### Prerequisites

 - **Docker** installed and configured(https://www.docker.com/)
 - **PMD** installed and configured: [https://pmd.github.io/](https://pmd.github.io/)
 - **Python 3.7+** installed
 - **Git** installed
 - **java 11+** installed

###  Installation Steps 

 **1. **To install Docker, follow the official documentation:**
 (**Add Docker's official GPG key**:)**
```bash
        sudo apt-get update
        sudo apt-get install ca-certificates curl
        sudo install -m 0755 -d /etc/apt/keyrings
        sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
        sudo chmod a+r /etc/apt/keyrings/docker.asc
```
( **Add the repository to Apt sources**:)
```
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
    $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
```
(**To install the latest version, run**:)
``` bash
     sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
(**Check docker installation**)
``` bash
    sudo docker version
    sudo docker run hello-world
    sudo docker images
    sudo docker ps -a
    sudo usermod -aG docker ${USER}
    docker run  --rm -d -p 8080:80 --name my-nginx nginx
```
**2. Install dependencies including git, java, python**

``` bash 
    sudo apt-get install git
    sudo apt install -y openjdk-11-jdk
    sudo apt install -y python3 python3-pip
    pip install gitpython
```

 **3. Environment Preparation and Check**

``` bash 
    sudo mkdir -p /home/user/pmd_miner 
    cd /home/user/pmd_miner 
    ls -ld /home/user/pmd_miner 
    echo $USER
    sudo chown -R $USER:$USER
```

**4. Modify *Dockerfile* (including PMD installatin and remote repository with PMD analysis code inside)**

```bash 
    cd /home/user/pmd_miner 
    nano Dockerfile
```

The *Dockerfile* :
``` 
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


# Set PMD permissions and path
#RUN chmod +x /app/pmd/pmd-bin-7.15.0/bin/pmd && \
    #chmod +x /app/pmd/pmd-bin-7.15.0/bin/pmd.bat

# Set PMD path
ENV PMD_HOME=/opt/pmd-bin-${PMD_VERSION}
ENV PATH="$PMD_HOME/bin:$PATH"

# clone  my github 
RUN git clone https://github.com/Lbyrigitte/pmd-analysis.git /app

# Copy requirements file
#COPY requirements.txt .

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
```

 **5. Build the docker image**

   `docker build --progress=plain -t pmd-analyzer .`
**If the warning is like:current commit information was not captured by the build: failed to read current commit information with git rev-parse --is-inside-work-tree.It means this directory is not a git repository but it doesn't affect the execution.To avoid it:**
  
  `DOCKER_BUILDKIT=0 docker build --progress=plain -t pmd-analyzer.`

**6. Test docker container**

`docker run -it --rm --entrypoint /bin/bash pmd-analyzer`
 `java -version`
 `python3 --version`
 `pmd --version`
**7. Test docker container clone conditions**
`docker run -it --rm --entrypoint /bin/bash pmd-analyzer `
`ls /app`

**If it shows the same content as the remote repository,the clone is successful.**

### Execution

 **1. Docker run**
``` 
# 1.Run analysis to analyze remote repositories(Linux path example)
**Outside the container**
docker run --rm \
-v $(pwd)/output:/app/output \
pmd-analyzer \
https://github.com/apache/commons-lang.git \
--ruleset rulesets/java/quickstart.xml \
--output-dir /app/output \
--pmd-path /opt/pmd-bin-7.15.0 \
--skip-download \
--max-commits 10 \
--verbose

**Inside the container(Should run in the container)**
python /app/main.py https://github.com/apache/commons-lang.git \
--ruleset /opt/pmd-bin-7.15.0/rulesets/java/quickstart.xml \
--output-dir /app/output \
--pmd-path /opt/pmd-bin-7.15.0 \
--skip-download \
--max-commits 10
```
- **Parameters can be changed **
**--max-commits** 
**--ruleset (You can change the self-selected paramenters of the officiaol rulesets like: quickstart.xml, bestpractices.xml, codestyle.xml...etc)**

## Output

 **1. Output Format**

 Commit level data (`output/commits/*.json`)
- Commit information (hash, author, date, message)
- Java file statistics (number, number of lines, file list)
- PMD analysis results (number of violations, detailed violation information)
- Calculation statistics (violation density, quality ratio, etc.)

 **2. Summary data (`output/summary.json`)**
- Basic information of the warehouse
- Number and average statistics of Java files
- Average statistics of warnings
- Rules violation statistics
- Time trend analysis
 
 **3. View the results**
 - **View summary results**

 ` cat output/summary.json` 

 - **View commit details**

` ls output/commits/`
` cat output/commits/6627f7ad.json`

 - **View logs**

` cat output/logs/*.log`
 
 **4. Format Description**
#### Top-level fields
- **`location`**: The repository path or URL to analyze
- **`stat_of_repository`**: Repository statistics
- **`stat_of_warnings`**: Warning statistics

#### Repository Statistics(`stat_of_repository`)

- **`number_of_commits`**: Total number of commits analyzed
- **`avg_of_num_java_files`**: Average number of Java files
- **`avg_of_num_warnings`**: Average number of warnings

#### Warning Statistics (`stat_of_warnings`)
Lists total violations by rule name:

- **`EmptyCatchBlock`**: Number of empty catch block violations
- **`SimplifyBooleanReturns`**: Number of Boolean return simplification violations
- **`UnusedLocalVariable`**: Number of unused local variable violations
- **`SystemPrintln`**: Number of System.out.println violations
- **`UnnecessaryReturn`**: Number of unnecessary return violations

#### Summary.json file in flat format:
```json
{
  "location": "https://github.com/apache/commons-lang.git",
  "stat_of_repository": {
    "number_of_commits": 10,
    "avg_of_num_java_files": 27.0,
    "avg_of_num_warnings": 18.7
  },
  "stat_of_warnings": {
    "EmptyCatchBlock": 99,
    "SimplifyBooleanReturns": 18,
    "UnusedLocalVariable": 70
  }
}
```
## Output description
### Structure
output/    
├── commits/ # Detailed analysis of each commit    
│         ├── abc123.json # Commit hash.json    
│         └── def456.json    
├── summary.json # Summary statistics    
└── logs/ # Log files    

## Performance
**1.Target Performance**: ≤1 second/commit
**2.Docker run**: ≤1 second/commit(0.6second with quickstart.xml)

## Image management

 - View images

    `docker images static-analyzer ` 

  - delete images

    `docker rmi static-analyzer ` 


 - Clean up all unused resources

    `docker system prune -a`

  
## Debug

 - Enter container debugging

`docker run -it --rm --entrypoint /bin/bash pmd-analyzer ` 
  

 - View files in container

`docker run --rm --entrypoint pmd-analyzer ls -la /app/  `
  

 - Check PMD installation

`docker run --rm --entrypoint pmd-analyzer /app/pmd/pmd-bin-7.15.0/bin/pmd --version  `


## Contributions

Welcome to submit issues and pull requests to improve this project.



## License

This project uses the MIT license.
