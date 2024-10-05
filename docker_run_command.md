To run Docker Compose with a specific compose file and the `--build` option to force a rebuild of the images, you can use the following command:

```bash
docker compose -f docker-compose-debug.yml up --build
```

### Explanation:
- **`-f docker-compose-prod.yml`**: Specifies the compose file to use. Replace `docker-compose-prod.yml` with `docker-compose-debug.yml` or any other file as needed.
- **`up`**: Brings up the services defined in the compose file.
- **`--build`**: Forces a rebuild of the images, even if they are already cached.

This command will use the specified Docker Compose file, rebuild all necessary images, and bring up the services accordingly.