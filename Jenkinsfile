pipeline {
    agent any
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Python') {
            steps {
                sh 'python3 --version'
                sh 'python3 -m venv venv'
                sh 'venv/bin/pip install --upgrade pip setuptools wheel'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                sh 'venv/bin/pip install -r requirements.txt'
            }
        }
        
        stage('Run Tests') {
            steps {
                sh 'venv/bin/pytest src/tests/ -v'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t imagenet-classifier .'
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