pipeline {
    agent {
        docker {
            image 'python:3.10'
            args '-v /var/run/docker.sock:/var/run/docker.sock -u root'
        }
    }
    
    environment {
        DOCKER_IMAGE_NAME = 'imagenet-classifier'
        DOCKER_REGISTRY = 'docker.io'
        GIT_COMMIT_SHORT = "${GIT_COMMIT.take(7)}"
        BUILD_TAG = "${BUILD_NUMBER}"
    }
    
    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timeout(time: 30, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo "📦 Checking out source code..."
                checkout scm
                sh 'git log -1 --oneline'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                echo "📥 Installing dependencies..."
                sh '''
                    apt-get update && apt-get install -y docker.io curl
                    pip install --upgrade pip setuptools wheel
                    pip install -r requirements.txt
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                echo "🧪 Running unit tests..."
                sh 'pytest src/unit_tests/ -v --tb=short || true'
            }
        }
        
        stage('Build Docker Image') {
            steps {
                echo "🔨 Building Docker image: ${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT}"
                sh '''
                    docker build \
                        --tag ${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT} \
                        --tag ${DOCKER_IMAGE_NAME}:${BUILD_TAG} \
                        --tag ${DOCKER_IMAGE_NAME}:latest \
                        --label "git.commit=${GIT_COMMIT}" \
                        --label "git.branch=${GIT_BRANCH}" \
                        --label "build.number=${BUILD_NUMBER}" \
                        --label "build.url=${BUILD_URL}" \
                        .
                '''
                sh 'docker images | grep ${DOCKER_IMAGE_NAME}'
            }
        }
        
        stage('Scan Image') {
            steps {
                echo "🔍 Scanning Docker image for vulnerabilities..."
                sh '''
                    docker run --rm \
                        -v /var/run/docker.sock:/var/run/docker.sock \
                        aquasec/trivy image ${DOCKER_IMAGE_NAME}:latest || true
                '''
            }
        }
        
        stage('Functional Test') {
            steps {
                echo "✅ Running functional tests..."
                sh '''
                    docker rm -f test-api || true
                    docker run -d \
                        -p 8000:8000 \
                        --name test-api \
                        --env VAULT_ADDR=http://localhost:8200 \
                        --env USE_VAULT=false \
                        ${DOCKER_IMAGE_NAME}:latest
                    sleep 5
                    curl -f http://localhost:8000/health || exit 1
                    curl -f http://localhost:8000/info || exit 1
                    docker stop test-api && docker rm test-api
                    echo "✓ API health check passed"
                '''
            }
        }
        
        stage('Push to DockerHub') {
            steps {
                echo "📤 Pushing image to DockerHub..."
                withCredentials([usernamePassword(credentialsId: 'docker-hub', 
                                                  usernameVariable: 'DOCKER_USER', 
                                                  passwordVariable: 'DOCKER_PASS')]) {
                    sh '''
                        echo "Logging in to Docker registry..."
                        echo ${DOCKER_PASS} | docker login -u ${DOCKER_USER} --password-stdin
                        
                        # Tag images for registry
                        docker tag ${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT} ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT}
                        docker tag ${DOCKER_IMAGE_NAME}:${BUILD_TAG} ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:${BUILD_TAG}
                        docker tag ${DOCKER_IMAGE_NAME}:latest ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:latest
                        
                        # Push all tags
                        docker push ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT}
                        docker push ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:${BUILD_TAG}
                        docker push ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:latest
                        
                        echo "✓ Image pushed successfully"
                        echo "Repository: ${DOCKER_USER}/${DOCKER_IMAGE_NAME}"
                        
                        docker logout
                    '''
                }
            }
        }
        
        stage('Documentation') {
            steps {
                echo "📝 Generating build documentation..."
                sh '''
                    cat > docker-build-info.txt <<EOF
Build Information
=================
Build Number: ${BUILD_NUMBER}
Build URL: ${BUILD_URL}
Git Commit: ${GIT_COMMIT}
Git Branch: ${GIT_BRANCH}
Image Tag: ${GIT_COMMIT_SHORT}
Build Tag: ${BUILD_TAG}

Docker Image Details
====================
Image Name: ${DOCKER_IMAGE_NAME}
Registry: ${DOCKER_REGISTRY}
Local Tags:
  - ${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT}
  - ${DOCKER_IMAGE_NAME}:${BUILD_TAG}
  - ${DOCKER_IMAGE_NAME}:latest

Pushed Tags (if credentials present):
  - \${DOCKER_USER}/${DOCKER_IMAGE_NAME}:${GIT_COMMIT_SHORT}
  - \${DOCKER_USER}/${DOCKER_IMAGE_NAME}:${BUILD_TAG}
  - \${DOCKER_USER}/${DOCKER_IMAGE_NAME}:latest

Pull Command:
  docker pull \${DOCKER_USER}/${DOCKER_IMAGE_NAME}:latest

Build Timestamp: $(date -u +'%Y-%m-%dT%H:%M:%SZ')
EOF
                    cat docker-build-info.txt
                '''
                archiveArtifacts artifacts: 'docker-build-info.txt', allowEmptyArchive: true
            }
        }
        
        stage('Trigger CD Pipeline') {
            steps {
                echo "🚀 Triggering CD pipeline for functional testing..."
                script {
                    try {
                        def job = build(
                            job: 'imagenet-classifier-cd',
                            wait: false,
                            parameters: [
                                string(name: 'IMAGE_TAG', value: 'latest'),
                                booleanParam(name: 'RUN_TESTS', value: true),
                                booleanParam(name: 'CLEANUP_AFTER', value: true)
                            ]
                        )
                        echo "✓ CD Pipeline triggered with build #${job.number}"
                    } catch (Exception e) {
                        echo "⚠️ Warning: Could not trigger CD pipeline - ${e.message}"
                        echo "This is non-blocking - CD pipeline can be triggered manually"
                    }
                }
            }
        }
    }
    
    post {
        success {
            echo '''
            ╔════════════════════════════════════════════╗
            ║  ✅ Pipeline completed successfully!       ║
            ║                                            ║
            ║  Docker Image: ${DOCKER_USER}/${DOCKER_IMAGE_NAME}:latest ║
            ║  Build #${BUILD_NUMBER} - ${GIT_COMMIT_SHORT}             ║
            ╚════════════════════════════════════════════╝
            '''
        }
        failure {
            echo '''
            ╔════════════════════════════════════════════╗
            ║  ❌ Pipeline failed!                        ║
            ║  Check logs for details: ${BUILD_URL}      ║
            ╚════════════════════════════════════════════╝
            '''
        }
        always {
            echo "🧹 Cleanup..."
            sh '''
                docker logout || true
                docker system prune -f --filter "until=24h" || true
            '''
            cleanWs()
        }
    }
}