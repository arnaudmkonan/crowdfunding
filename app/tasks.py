from celery import Celery

celery = Celery('tasks', broker='amqp://guest:guest@rabbitmq:5672//')

@celery.task
def process_payment(project_id: int, amount: float):
    # Implement payment processing logic here
    print(f"Processing payment of {amount} for project {project_id}")
    # Update project's current_amount in the database
