# Deployment

----

This folder contains scripts to use on the production machine, which runs Debian 8.7 (jessie). 

## Instructions

If you need access to the production machine ("`prod`"), please contact the project manager. Once you log into `prod` as the `root` user, perform the following in order to quickly deploy the project:

1. Input `source sob_on`. This will activate the virtual environment and `cd` you into the `manage.py` folder. It's a good shortcut.
2. Input `deploy/deploy_script`. This will perform the following:

    - `git pull origin master`
    - `python manage.py collectstatic --noinput`
    - `service restart gunicorn`
    - `service restart nginx`

    * If `deploy/deploy_script` does not work for you, then either you don't have access rights or the `deploy_script` file has not been made executable. Try the following to make it executable: `chmod +x deploy/deploy_script` (assuming you're in the `manage.py` directory).

3. That's all you have to do in order to grab the latest from the `master` branch on `git` and make your changes live.

## Important directories:
1. The top-level of the project is located inside `/home/shoutourbiz/shoutourbiz_site/project`
2. `gunicorn` is used to run `Django`. It feeds into a `socket`
3. `nginx` is used as the reverse proxy to direct external web requests to the `socket`.