import requests
import json

import model
import pyrebase
from auth import FirebaseAuth
from http_artifact_store import HTTPArtifactStore

import logging
logging.basicConfig()


class HTTPProvider(object):
    """Data provider communicating with API server."""

    def __init__(self, config, verbose=10, blocking_auth=True):
        # TODO: implement connection
        self.url = config.get('serverUrl')
        self.verbose = verbose
        self.logger = logging.getLogger('HTTPProvider')
        self.logger.setLevel(self.verbose)

        self.auth = None
        self.app = pyrebase.initialize_app(config)
        guest = config.get('guest')
        if not guest and 'serviceAccount' not in config.keys():
            self.auth = FirebaseAuth(self.app,
                                     config.get("use_email_auth"),
                                     config.get("email"),
                                     config.get("password"),
                                     blocking_auth)

    def add_experiment(self, experiment):
        headers = self._get_headers()
        request = requests.post(
            self.url + '/api/add_experiment',
            headers=headers,
            data=json.dumps({"experiment": experiment.__dict__}))

        self._raise_detailed_error(request)
        artifacts = request.json()['artifacts']

        self._update_artifacts(experiment, artifacts)

    def _update_artifacts(self, experiment, artifacts):
        for tag, art in experiment.artifacts.iteritems():
            art['key'] = artifacts[tag]['key']
            art['qualified'] = artifacts[tag]['qualified']
            art['bucket'] = artifacts[tag]['bucket']

            HTTPArtifactStore(artifacts[tag]['url'],
                              artifacts[tag]['timestamp'],
                              self.verbose) \
                .put_artifact(art)

    def delete_experiment(self, experiment):
        if isinstance(experiment, basestring):
            key = experiment
        else:
            key = experiment.key

        headers = self._get_headers()
        request = requests.post(self.url + '/api/delete_experiment',
                                headers=headers,
                                data=json.dumps({"key": key})
                                )
        self._raise_detailed_error(request)

    def get_experiment(self, experiment, getinfo='True'):
        if isinstance(experiment, basestring):
            key = experiment
        else:
            key = experiment.key

        headers = self._get_headers()
        request = requests.post(self.url + '/api/get_experiment',
                                headers=headers,
                                data=json.dumps({"key": key})
                                )

        self._raise_detailed_error(request)
        return model.experiment_from_dict(request.json()['experiment'])

    def start_experiment(self, experiment):
        self.checkpoint_experiment(experiment)
        if isinstance(experiment, basestring):
            key = experiment
        else:
            key = experiment.key

        headers = self._get_headers()
        request = requests.post(self.url + '/api/start_experiment',
                                headers=headers,
                                data=json.dumps({"key": key})
                                )
        self._raise_detailed_error(request)

    def stop_experiment(self, experiment):
        key = experiment.key

        headers = self._get_headers()
        request = requests.post(self.url + '/api/stop_experiment',
                                headers=headers,
                                data=json.dumps({"key": key})
                                )
        self._raise_detailed_error(request)

    def finish_experiment(self, experiment):
        self.checkpoint_experiment(experiment)
        if isinstance(experiment, basestring):
            key = experiment
        else:
            key = experiment.key

        headers = self._get_headers()
        request = requests.post(self.url + '/api/finish_experiment',
                                headers=headers,
                                data=json.dumps({"key": key})
                                )
        self._raise_detailed_error(request)

    def get_user_experiments(self, user):
        raise NotImplementedError()

    def get_projects(self):
        raise NotImplementedError()

    def get_project_experiments(self):
        raise NotImplementedError()

    def get_artifacts(self):
        raise NotImplementedError()

    def get_artifact(self, artifact, only_newer='True'):
        return HTTPArtifactStore(artifact['url'], self.verbose) \
            .get_artifact(artifact)

    def get_users(self):
        raise NotImplementedError()

    def checkpoint_experiment(self, experiment):
        if isinstance(experiment, basestring):
            key = experiment
            experiment = self.get_experiment(key)
        else:
            key = experiment.key

        headers = self._get_headers()
        request = requests.post(self.url + '/api/checkpoint_experiment',
                                headers=headers,
                                data=json.dumps({"key": key})
                                )

        self._raise_detailed_error(request)
        artifacts = request.json()['artifacts']

        self._update_artifacts(experiment, artifacts)

    def refresh_auth_token(self, email, refresh_token):
        raise NotImplementedError()

    def get_auth_domain(self):
        raise NotImplementedError()

    def _get_headers(self):
        headers = {"content-type": "application/json"}
        if self.auth:
            headers["Authorization"] = "Firebase " + self.auth.get_token()
        return headers

    def _raise_detailed_error(self, request):
        if request.status_code != 200:
            raise ValueError(request.message)

        data = request.json()
        if data['status'] == 'ok':
            return

        raise ValueError(data['status'])



    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass
