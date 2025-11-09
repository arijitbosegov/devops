pipeline {
    agent any

    environment {
        DOCKERHUB = "loutuhal"
        APPNAME   = "flask-app"
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    def imageTag = "${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
                    sh "docker build -t ${DOCKERHUB}/${APPNAME}:${imageTag} ."
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    sh "docker run --rm ${DOCKERHUB}/${APPNAME}:${env.BRANCH_NAME}-${env.BUILD_NUMBER} pytest || true"
                }
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DOCKER_USER', passwordVariable: 'DOCKER_PASS')]) {
                    sh "echo $DOCKER_PASS | docker login -u $DOCKER_USER --password-stdin"
                    sh "docker push ${DOCKERHUB}/${APPNAME}:${env.BRANCH_NAME}-${env.BUILD_NUMBER}"
                }
            }
        }
    }

    post {
        success {
            echo '✅ Build succeeded!'
        }
        failure {
            echo '❌ Build failed.'
        }
    }
}
