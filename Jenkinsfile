pipeline {
    agent {
        docker {
            image 'python:3.10'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        stage('Install Dependencies') {
            steps {
                sh 'apt-get update && apt-get install -y docker.io curl'
                sh 'pip install --upgrade pip setuptools wheel'
                sh 'pip install -r requirements.txt'
            }
        }
        stage('Unit Tests') {
            steps {
                sh 'pytest src/unit_tests/ -v'
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t imagenet-classifier .'
            }
        }
        stage('Functional Test') {
            steps {
                sh 'docker run -d -p 8000:8000 --name test-api imagenet-classifier'
                sh 'sleep 5'
                sh 'curl -f http://localhost:8000/health || exit 1'
                sh 'echo "Functional test passed: API is healthy"'
                sh 'docker stop test-api && docker rm test-api'
            }
        }
    }
    post {
        success {
            echo 'Pipeline completed successfully! ✅'
        }
        failure {
            echo 'Pipeline failed! ❌'
        }
    }
}