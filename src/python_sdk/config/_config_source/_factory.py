from python_sdk.config._config_source import _aws_parameter_store_document
from python_sdk.config._config_source import _aws_secrets_manager_secret
from python_sdk.config._config_source import _environment_variables
from python_sdk.config._config_source import _file_object
from python_sdk.config._config_source import _local_file
from python_sdk.config._config_source import _protocol
from python_sdk.config._config_source import _remote_http_file
from python_sdk.config._config_source import _s3_file
from python_sdk.config._config_source import _static_dictionary

_IMPLEMENTATIONS: dict[str, type[_protocol.ConfigSource]] = {
    _aws_parameter_store_document.AWSParameterStoreDocument.TYPE: _aws_parameter_store_document.AWSParameterStoreDocument,
    _aws_secrets_manager_secret.AWSSecretsManagerSecret.TYPE: _aws_secrets_manager_secret.AWSSecretsManagerSecret,
    _environment_variables.EnvironmentVariables.TYPE: _environment_variables.EnvironmentVariables,
    _file_object.FileObject.TYPE: _file_object.FileObject,
    _local_file.LocalFile.TYPE: _local_file.LocalFile,
    _remote_http_file.RemoteHTTPFile.TYPE: _remote_http_file.RemoteHTTPFile,
    _s3_file.S3File.TYPE: _s3_file.S3File,
    _static_dictionary.StaticDictionary.TYPE: _static_dictionary.StaticDictionary,
}


def register_implementation(implementation: type[_protocol.ConfigSource]) -> None:
    _IMPLEMENTATIONS[implementation.TYPE] = implementation


def config_source(type: str) -> _protocol.ConfigSource:
    if type not in _IMPLEMENTATIONS:
        raise NotImplementedError(type)
    implementation = _IMPLEMENTATIONS[type]
    return implementation()
