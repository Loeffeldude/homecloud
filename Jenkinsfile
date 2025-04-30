pipeline {
    agent {
        kubernetes {
            yaml '''
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                  - name: docker
                    image: docker:dind
                    securityContext:
                      privileged: true
                    env:
                    - name: DOCKER_TLS_CERTDIR
                      value: ""
                    tty: true
            '''
            defaultContainer 'docker'
        }
    }

    environment {
        REGISTRY = "cr.lffl.me"
        REGISTRY_CREDENTIALS_ID = 'cr-lffl-credentials'
    }

    parameters {
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Tag for the images')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Push Images') {
            steps {
                withDockerRegistry([credentialsId: REGISTRY_CREDENTIALS_ID, url: "https://${REGISTRY}"]) {
                    sh """
                        dockerd &
                        sleep 5
                        docker build -t ${REGISTRY}/webdav-mounter:${params.IMAGE_TAG} docker/webdav-mounter/
                        docker push ${REGISTRY}/webdav-mounter:${params.IMAGE_TAG}
                    """
                }
            }
        }
    }

    post {
        always {
            deleteDir()
        }
    }
}
