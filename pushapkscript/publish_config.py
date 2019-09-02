import logging

log = logging.getLogger(__name__)


def _handle_legacy_google_track(google_track):
    if google_track == 'rollout':
        log.warn('Using "rollout" as the Google Play Track is deprecated, please specify the '
                 'target track that you would like to rollout to, instead. Assuming you meant '
                 '"production" for this task.')
        return 'production'
    return google_track


def _get_single_google_app_publish_config(product_config, payload):
    publish_config = product_config['app']
    rollout_percentage = payload.get('rollout_percentage')
    google_track = payload['channel']
    google_track = _handle_legacy_google_track(google_track)
    return {
        'target_store': 'google',
        'certificate_alias': publish_config['certificate_alias'],
        'username': publish_config['service_account'],
        'secret': publish_config['credentials_file'],
        'package_names': publish_config['package_names'],
        'google_track': google_track,
        'google_rollout_percentage': rollout_percentage,
    }


def _get_google_app_by_scope_publish_config(product_config, payload, scope_product):
    publish_config = product_config['apps'][scope_product]
    rollout_percentage = payload.get('rollout_percentage')
    google_track = payload.get('google_play_track', publish_config['default_track'])
    google_track = _handle_legacy_google_track(google_track)
    return {
        'target_store': 'google',
        'certificate_alias': publish_config['certificate_alias'],
        'username': publish_config['service_account'],
        'secret': publish_config['credentials_file'],
        'package_names': publish_config['package_names'],
        'google_track': google_track,
        'google_rollout_percentage': rollout_percentage,
    }


def _get_channel_publish_config(product_config, payload):
    publish_config = product_config['apps'][payload['channel']]
    target_store = payload.get('target_store')

    # Determine the target store. If "target_store" isn't provided on the task payload,
    # attempt to automatically determine it by checking if the channel only supports a single
    # target - if so, then use that target store.
    if target_store:
        if not publish_config.get(target_store):
            raise ValueError(
                'Task had `target_store` set to "{}", but the "{}" channel does not support '
                'that target'.format(target_store, payload['channel'])
            )
    elif publish_config.get('google') and not publish_config.get('amazon'):
        target_store = 'google'
    elif publish_config.get('amazon') and not publish_config.get('google'):
        target_store = 'amazon'
    else:
        raise ValueError('The "{}" channel supports "amazon" and "google" as targets, but '
                         '`target_store` was not provided in the task payload to disambiguate')

    store_config = publish_config[target_store]
    if target_store == 'amazon':
        if payload.get('google_play_track') or payload.get('rollout_percentage'):
            raise ValueError('The "google_play_track" and "rollout_percentage" properties are '
                             'not allowed if the target store is "amazon"')

        return {
            'target_store': 'amazon',
            'certificate_alias': publish_config['certificate_alias'],
            'username': store_config['client_id'],
            'secret': store_config['client_secret'],
            'package_names': publish_config['package_names'],
        }
    else:
        rollout_percentage = payload.get('rollout_percentage')
        google_track = payload.get('google_play_track', store_config['default_track'])
        google_track = _handle_legacy_google_track(google_track)

        return {
            'target_store': 'google',
            'certificate_alias': publish_config['certificate_alias'],
            'username': store_config['service_account'],
            'secret': store_config['credentials_file'],
            'package_names': publish_config['package_names'],
            'google_track': google_track,
            'google_rollout_percentage': rollout_percentage,
        }


def get_publish_config(product_config, payload, scope_product):
    override_channel_model = product_config.get('override_channel_model')
    if override_channel_model == 'single_google_app':
        # Focus uses a single Google app and the "tracks" feature to represent different channels,
        # rather than a separate app-per-channel. So, Focus is configured with "single_google_app"
        return _get_single_google_app_publish_config(product_config, payload)

    elif override_channel_model == 'choose_google_app_with_scope':
        # Fennec only targets google, but doesn't provide the channel in the payload. We need
        # to leverage the legacy strategy of inferring the channel from the scope, then choosing
        # the Google app accordingly
        return _get_google_app_by_scope_publish_config(product_config, payload, scope_product)

    else:
        # The common configuration will have "channel" specified in the payload, which is used
        # to choose the app to deploy to. It can support both Google and Amazon as a target store.
        return _get_channel_publish_config(product_config, payload)
