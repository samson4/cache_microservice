.DEFAULT_GOAL := help

.PHONY: help build run test stop down clean logs

help: ## Show available commands
	@printf "Available commands:\n"
	@printf "  make build  Build the application image\n"
	@printf "  make run    Build and run the application\n"
	@printf "  make test   Run the unit tests in a container\n"
	@printf "  make stop   Stop application containers\n"
	@printf "  make down   Stop and remove application containers\n"
	@printf "  make clean  Remove containers, images, and persisted data\n"
	@printf "  make logs   Follow application logs\n"

build: ## Build the application image
	docker compose build

run: ## Build and run the application
	docker compose up --build --detach

test: ## Run the unit tests in a container
	docker build --target test --tag payload-cache-service-test --file docker/dockerfile .
	docker run --rm --env-file .env payload-cache-service-test

stop: ## Stop application containers
	docker compose stop

down: ## Stop and remove application containers
	docker compose down --remove-orphans

clean: ## Remove containers, images, and persisted data
	docker compose down --volumes --remove-orphans --rmi local

logs: ## Follow application logs
	docker compose logs --follow api
