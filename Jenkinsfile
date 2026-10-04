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
                sh 'python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r backend/requirements.txt && python -m pytest backend/tests'
            }
        }

        stage('Frontend dependencies and build') {
            steps {
                sh 'npm ci --prefix frontend && npm run build --prefix frontend'
            }
        }
    }
}