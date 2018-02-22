from keywords.TestServerAndroid import TestServerAndroid
from keywords.TestServeriOS import TestServeriOS
from keywords.TestServerNetMono import TestServerNetMono
from keywords.TestServerNetMsft import TestServerNetMsft


class TestServerFactory:

    @staticmethod
    def validate_version_build(version_build):
        if version_build is None:
            raise ValueError("Make sure you provide a version / build!")

        if len(version_build.split("-")) != 2:
            raise ValueError("Make sure your version_build follows the format: 2.0.0-576")

    @staticmethod
    def validate_platform(platform):
        valid_platforms = ["android", "ios", "net-mono", "net-msft"]
        if platform not in valid_platforms:
            raise ValueError("Unsupported 'platform': {}".format(platform))

    @staticmethod
    def validate_host(host):
        if host is None:
            raise ValueError("Make sure you provide a host!")

    @staticmethod
    def validate_port(port):
        if port is None:
            raise ValueError("Make sure you provide a port!")

    @staticmethod
    def create(platform, version_build, host, port, community_enabled=None):

        TestServerFactory.validate_platform(platform)
        TestServerFactory.validate_version_build(version_build)
        TestServerFactory.validate_host(host)
        TestServerFactory.validate_port(port)

        if platform == "android":
            return TestServerAndroid(version_build, host, port)
        elif platform == "ios":
            return TestServeriOS(version_build, host, port, community_enabled)
        elif platform == "net-mono":
            return TestServerNetMono(version_build, host, port)
        elif platform == "net-msft":
            return TestServerNetMsft(version_build, host, port)
        else:
            raise NotImplementedError("Test server does not support this version")