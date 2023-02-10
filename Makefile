YML	=	srcs/docker-compose.yml

all: 
	docker-compose -f $(YML) up

build: 
	docker-compose -f $(YML) up --build

down:
	docker-compose -f $(YML) down

re: fclean all

clean:
	docker-compose -f $(YML) rm -f

fclean:	clean
	docker volume rm esdata

.PHONY: all build re down clean fclean
