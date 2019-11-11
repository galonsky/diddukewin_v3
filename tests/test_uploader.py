import pytest
from botocore.exceptions import ClientError

from ddw.uploader import head_object, md5_content, should_upload_new, upload


@pytest.fixture
def client_mock(mocker):
    return mocker.patch("ddw.uploader.client")


class TestHeadObject:
    def test_returns_result_of_head(self, client_mock):
        client_mock.head_object.return_value = {"foo": "bar"}
        assert head_object("bucket", "key") == {"foo": "bar"}

    def test_when_client_error_raised_returns_empty_dict(self, client_mock):
        client_mock.head_object.side_effect = ClientError({}, "bar")
        assert head_object("bucket", "key") == {}


class TestMd5Content:
    def test_works_on_string(self):
        content = "foobar"
        hexdigest = md5_content(content)
        assert len(hexdigest) == 32


class TestShouldUploadNew:
    @pytest.fixture
    def head_object_mock(self, mocker):
        return mocker.patch("ddw.uploader.head_object")

    def test_when_no_etag_returns_true(self, head_object_mock):
        head_object_mock.return_value = {}
        assert should_upload_new("foo", "bar", "baz")

    def test_when_etag_matches_returns_false(self, head_object_mock):
        head_object_mock.return_value = {"ETag": '"{}"'.format(md5_content("foo"))}
        assert not should_upload_new("foo", "bar", "baz")

    def test_when_etag_doesnt_match_returns_true(self, head_object_mock):
        head_object_mock.return_value = {
            "ETag": '"{}"'.format(md5_content("basafasdasdf"))
        }
        assert should_upload_new("foo", "bar", "baz")


class TestUpload:
    @pytest.fixture
    def should_upload_mock(self, mocker):
        return mocker.patch("ddw.uploader.should_upload_new")

    def test_when_should_not_upload_does_not(self, client_mock, should_upload_mock):
        should_upload_mock.return_value = False
        upload("food", "bar", "gaz")
        client_mock.put_object.assert_not_called()

    def test_when_should_upload_calls_put(self, client_mock, should_upload_mock):
        should_upload_mock.return_value = True
        upload("food", "bar", "gaz")
        client_mock.put_object.assert_called_once_with(
            Bucket="bar", Key="gaz", Body="food", ContentType="text/html"
        )
