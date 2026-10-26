***Wink_Ai_Gatherer - a script project for the WINK online cinema that allows generating reports on competitor updates across app stores.***

* The **AppIds_list.yaml** file contains the app IDs of competitors in three stores: App Store, Google Play, Ru Store
* Use **main.py** to run the script

By default, the cycle runs once every 7 days, but this can be changed in docker-compose.yml

Setup
--------------------------------------------------

### `.env` Setup

How to create a local `.env` from the template:

```bash
cp .env.example .env
```

### Installing all libraries in your environment:

```bash
pip install -r requirements.txt
```

### Start the docker container for the script to work:

```bash
docker compose up --build # launch the container itself
```

### Run a one-time test:

```bash
RUN_ONCE=1 docker compose up --build
```

### View the report:

```bash
cat competitor_report.txt
```
--------------------------------------------------
Environment variables needed:

```env
ROUTER_AI_API_KEY
ROUTER_AI_MODEL
ROUTER_AI_BASE_URL
```
