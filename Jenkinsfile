pipeline {
  agent any

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
      parallel {
        stage('webdav-mounter') {
          steps {
            script {
              def imageName = "${REGISTRY}/webdav-mounter:${params.IMAGE_TAG}"
              def image = docker.build(imageName, "docker/webdav-mounter/")
              docker.withRegistry("https://${REGISTRY}", REGISTRY_CREDENTIALS_ID) {
                image.push()
              }
            }
          }
        }
      }
    }
  }

  post {
    always {
      cleanWs()
    }
  }
}
