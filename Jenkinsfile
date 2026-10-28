
pipeline {
    agent any

    options {
        timestamps()
    }

    environment {
        PYTHON_EXE = 'C:\\Users\\siddh\\AppData\\Local\\Programs\\Python\\Python313\\python.exe'
        DOCKER_EXE = 'C:\\Users\\siddh\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe'
        KUBECTL_EXE = 'C:\\Users\\siddh\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\kubectl.exe'
        KUBECONFIG = 'C:\\Users\\siddh\\.kube\\config'
    }

    stages {
        stage('Validate Version Branch') {
            steps {
                script {
                    def branch = env.BRANCH_NAME ?: 'v1'

                    if (!(branch in ['v1', 'v2', 'v3'])) {
                        error("Use the v1, v2 or v3 branch. Current: ${branch}")
                    }

                    env.IMAGE_TAG = branch
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                bat '"%PYTHON_EXE%" -m pip install -r requirements.txt'
            }
        }

        stage('Run Tests') {
            steps {
                bat '"%PYTHON_EXE%" -m pytest -v'
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

                    bat 'powershell -NoProfile -ExecutionPolicy Bypass -Command "$env:DOCKERHUB_TOKEN | & $env:DOCKER_EXE login -u $env:DOCKERHUB_USER --password-stdin"'

                    bat '"%DOCKER_EXE%" build -t %IMAGE_NAME% .'
                    bat '"%DOCKER_EXE%" push %IMAGE_NAME%'
                    bat '"%DOCKER_EXE%" logout'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                bat '"%KUBECTL_EXE%" apply -f k8s/%IMAGE_TAG%-deployment.yaml'
                bat '"%KUBECTL_EXE%" apply -f k8s/%IMAGE_TAG%-service.yaml'

                bat '"%KUBECTL_EXE%" set image deployment/pharmacy-%IMAGE_TAG% pharmacy=siddharthvr7/pharmacy-system:%IMAGE_TAG%'
                bat '"%KUBECTL_EXE%" rollout status deployment/pharmacy-%IMAGE_TAG% --timeout=180s'
            }
        }
    }

    post {
        success {
            echo "Pharmacy ${env.IMAGE_TAG} pipeline completed successfully."
        }
        failure {
            echo 'Pipeline failed. Check the stage logs.'
        }
    }
}
