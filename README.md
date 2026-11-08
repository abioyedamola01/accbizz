# Accbizz

A Django website for an accounting and business services firm. It has a public site for visitors and a private dashboard where staff manage the content, read enquiries, moderate testimonials and manage the team.

## Features

**Public site**
- Home, About, Services, Service detail, FAQs, Testimonials and Contact pages
- Contact form sent with fetch, with a success state
- Testimonials: an auto-sliding slider on the home page, a full testimonials page that loads in batches, and a form for visitors to submit their own (held for approval before it is shown)
- FAQs with a "Read more" modal that loads more questions in batches
- Light, dark and system themes, with no flash of the wrong theme on load
- Privacy-friendly analytics with [Umami](https://umami.is) (self-hosted)

**Staff dashboard** (`/users/staffs/dashboard/`)
- **Site**: company details, logos and favicon
- **Contents**: Home sections, About, Services, FAQs, Testimonials and Team, all editable in place
- **Communication**: contact form messages, with filters, mark as attended or unattended, and delete
- **Staffs**: add staff, change role, reset password, change email, remove or reinstate, and a per-staff activity log
- **Reports**: date-filtered enquiry summary, charts, response performance, site traffic from Umami, content health and staff activity
- **Profile**: avatar and personal details

**Staff accounts** (`/users/staffs/accounts/`)
- Login with a one-time code (OTP) sent by email
- Account creation from an emailed link (valid 24 hours), change password, reset password, and change email (a confirmation goes to the new address, a notice with a revert link to the old one)
- Two roles, Administrator and Staff, each backed by a permission group

**Interface behaviour**
- Toast messages for results and errors
- Every button and link disables itself when clicked, fades, shows a spinner and shows the not-allowed cursor, so nothing is submitted twice (`templates/components/_busy.html`)

## Tech stack

- Python 3.12+ and Django 6
- PostgreSQL, configured through `DATABASE_URL` (`psycopg2-binary`, `dj-database-url`)
- Tailwind CSS v4 and Flowbite v4, built with the Tailwind CLI
- WhiteNoise for static files, Gunicorn as the server
- Amazon S3 (or any S3-compatible storage) for uploaded images, through `django-storages` and `boto3`
- SMTP for email
- Umami for analytics

## Project structure

```
accbizz/
├── manage.py
├── build.sh                  # install, build CSS, collectstatic (for hosting platforms)
├── requirements.txt
├── package.json              # Tailwind scripts: dev, build
├── accbizz/                  # settings.py, urls.py, wsgi.py, asgi.py
├── main/                     # public site: pages, contact form, testimonials, FAQ batches
├── dashboard/                # dashboard views, content models, reports, Umami data
├── staffs/                   # custom user model, OTP login, roles and permissions, activity log
├── static/
│   ├── src/input.css         # Tailwind source
│   ├── css/base.css          # base styles imported by input.css
│   ├── css/output.css        # compiled file (generated, not in Git)
│   └── js/                   # base, ui, motion, loading, contact, dashboard*, communication, staffs ...
└── templates/
    ├── base/                 # main/, dashboard/ and staffs/ base layouts and shared partials
    ├── components/           # _button, _icon, _logo, _avatar, _busy ...
    ├── main/  dashboard/  staffs/
    ├── messages/             # email templates (OTP, account creation, email change, contact ...)
    └── errors/               # 400, 403, 403_csrf, 404, 429, 500
```

## Getting started

### 1. Clone and install

```bash
git clone https://github.com/abioyedamola01/accbizz.git
cd accbizz

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

npm install
```

### 2. Environment variables

Create a `.env` file in the project root (next to `manage.py`). Never commit it. A starting point is in `.env.example`.

| Variable | Purpose |
|---|---|
| `SECRET_KEY` | Django secret key |
| `ALLOWED_HOSTS` | Comma-separated hostnames, e.g. `localhost,127.0.0.1` |
| `DATABASE_URL` | Database connection, e.g. `postgres://user:pass@localhost:5432/accbizz` |
| `BASE_URL` | Public address of the site, used to build the links in emails |
| `DEFAULT_ADMINS` | Comma-separated emails that become the first administrators |
| `EMAIL_HOST`, `EMAIL_PORT` | SMTP server (`EMAIL_PORT` must be a number) |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | `True` or `False` |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | SMTP login (the host user is also the default site email) |
| `DEFAULT_FROM_EMAIL`, `SERVER_EMAIL` | Sender addresses |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Storage credentials |
| `AWS_STORAGE_BUCKET_NAME` | Bucket for uploaded images |
| `AWS_REGION` | Optional, defaults to `eu-central-1` |
| `AWS_ENDPOINT_URL_S3` | Optional, for S3-compatible providers |
| `UMAMI_API_URL`, `UMAMI_API_KEY` | Umami API, used by the Reports traffic section |
| `UMAMI_PUBLIC_WEBSITE_ID` | Umami website ID of the public site |

### 3. Database and first data

```bash
python manage.py migrate
python manage.py prod_system_setup
```

`prod_system_setup` is safe to run more than once. It creates the role groups and their permissions, creates the default content sections and the site record, and sends an account-creation email to every address in `DEFAULT_ADMINS`. Open the link in that email to set a password, then log in. Login always asks for an emailed code, so email must be working.

### 4. Build the CSS and run

```bash
npm run dev                       # Tailwind in watch mode (leave running)
python manage.py runserver        # in a second terminal
```

- Public site: http://127.0.0.1:8000/
- Staff login: http://127.0.0.1:8000/users/staffs/accounts/auth/login
- Dashboard: http://127.0.0.1:8000/users/staffs/dashboard/

### Local development notes

- `DEBUG` is set to `False` in `settings.py`, so Django will not serve error details or media locally. Change it to `True` on your machine only, and do not commit that.
- Uploaded images go to S3 (the default storage), so uploads need working `AWS_*` values or a change to `STORAGES` for local files.
- The Umami script tag in `templates/base/main/base.html` has the Umami address and website ID written into the file.

## Useful commands

| Command | What it does |
|---|---|
| `npm run build` | Builds a minified `static/css/output.css` |
| `python manage.py prod_system_setup` | One-time initial data setup (safe to re-run) |
| `python manage.py create_role_groups` | Creates the Administrator and Staff groups |
| `python manage.py set_permissions` | Assigns permissions to those groups |
| `python manage.py create_default_admin_staffs` | Sends account-creation emails to `DEFAULT_ADMINS` |

## Deployment

`build.sh` does the whole build: `npm ci`, `npm run build`, `pip install -r requirements.txt` and `collectstatic`. Point your host's build command at it and start the app with Gunicorn:

```bash
gunicorn accbizz.wsgi
```

Checklist:

- [ ] All variables from the table above are set on the host
- [ ] `ALLOWED_HOSTS` and `BASE_URL` match the live domain
- [ ] Run `python manage.py migrate` and `python manage.py prod_system_setup` once after the first deploy
- [ ] The storage bucket exists and is publicly readable for the image URLs
- [ ] Email credentials work, since staff login depends on them
- [ ] Umami URL, key and website IDs are correct


## License

Private project. 