pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Backend dependencies and tests') {
            steps {
                bat '''
if exist .venv rmdir /s /q .venv
if exist .venv exit /b 1
py -3.11 --version && py -3.11 -m venv .venv && .venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt && .venv\\Scripts\\python.exe -m pytest backend\\tests
'''
            }
        }

        stage('Frontend dependencies and build') {
            steps {
                bat 'cd /d "%WORKSPACE%\\frontend" && npm ci && npm run build'
            }
        }
    }
}