
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Validate Version Branch') {
            steps {
                script {
                    def branch = env.BRANCH_NAME ?: 'main'

                    if (!(branch in ['v1', 'v2', 'v3'])) {
                        error("Use the v1, v2 or v3 branch. Current: ${branch}")
                    }

                    env.IMAGE_TAG = branch
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat 'python -m pytest -v'
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    script {
                        env.IMAGE_NAME =
                            "${env.DOCKERHUB_USER}/pharmacy-system:${env.IMAGE_TAG}"
                    }

                    bat 'docker login -u "%DOCKERHUB_USER%" --password-stdin < nul'
                    bat 'powershell -NoProfile -Command "$env:DOCKERHUB_TOKEN | docker login -u $env:DOCKERHUB_USER --password-stdin"'

                    bat 'docker build -t %IMAGE_NAME% .'
                    bat 'docker push %IMAGE_NAME%'
                    bat 'docker logout'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-creds',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    bat 'kubectl apply -f k8s/%IMAGE_TAG%-deployment.yaml'
                    bat 'kubectl apply -f k8s/%IMAGE_TAG%-service.yaml'

                    bat 'kubectl set image deployment/pharmacy-%IMAGE_TAG% pharmacy=%DOCKERHUB_USER%/pharmacy-system:%IMAGE_TAG%'
                    bat 'kubectl rollout status deployment/pharmacy-%IMAGE_TAG% --timeout=180s'
                }
            }
        }
    }

    post {
        success {
            echo "Pharmacy ${env.IMAGE_TAG} pipeline completed successfully."
        }
        failure {
            echo "Pipeline failed. Check the stage logs."
        }
    }
}
