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
                bat 'python --version'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                bat 'pip install -r requirements.txt'
            }
        }
        
        stage('Run Tests') {
            steps {
                bat 'pytest src/tests/ -v'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                bat 'docker build -t imagenet-classifier .'
            }
        }
    }
}



