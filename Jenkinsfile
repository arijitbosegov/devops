pipeline {
  agent any
  environment {
    DOCKERHUB = ""
    APPNAME   = "flask-app"
  }

  stages {
    stage('Checkout') { steps { checkout scm } }

    stage('Set variables') {
      steps { script {
          if (env.BRANCH_NAME == 'master')       { env.APP_PATH = 'app_1' }
          else if (env.BRANCH_NAME == 'version1'){ env.APP_PATH = 'app_1.1' }
          else if (env.BRANCH_NAME == 'version2'){ env.APP_PATH = 'app_1.2' }
          else if (env.BRANCH_NAME == 'version3'){ env.APP_PATH = 'app_1.3' }
          else { env.APP_PATH = '.' }
          env.IMAGE = "/:-"
      } }
    }

    stage('Build Docker image') {
      steps { script {
          if (isUnix()) { sh "docker build -t  " }
          else { bat "docker build -t  " }
      } }
    }

    stage('Run tests inside container') {
      steps { script {
          if (isUnix()) { sh "docker run --rm  pytest --maxfail=1 -q" }
          else { bat "docker run --rm  pytest --maxfail=1 -q" }
      } }
    }

    stage('Docker login & push') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'docker-hub-creds', usernameVariable: 'DH_USER', passwordVariable: 'DH_PASS')]) {
          script {
            if (isUnix()) {
              sh "echo \ | docker login -u \ --password-stdin"
              sh "docker push "
            } else {
              bat "powershell -Command \"echo '%DH_PASS%' | docker login -u %DH_USER% --password-stdin\""
              bat "docker push "
            }
          }
        }
      }
    }

    stage('Optional: Tag release on master') {
      when { branch 'master' }
      steps {
        script {
          def rel = "v"
          if (isUnix()) {
            sh "git tag -a  -m 'Release ' || true"
            sh "git push origin  || true"
            sh "docker tag  /:"
            sh "echo \ | docker login -u \ --password-stdin"
            sh "docker push /:"
          } else {
            bat "git tag -a  -m \"Release \" || exit 0"
            bat "git push origin  || exit 0"
            bat "docker tag  /:"
            bat "docker login -u %DH_USER% -p %DH_PASS%"
            bat "docker push /:"
          }
        }
      }
    }
  }

  post { always { cleanWs() } failure { echo "Build failed" } }
}
