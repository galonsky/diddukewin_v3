import pytest
from atproto_client.models.blob_ref import BlobRef, IpldLink

from ddw.bluesky import LinkCard, Skeeter

BLOB = BlobRef(
    mime_type="image/png",
    size=9,
    ref=IpldLink(link="bafkreibme22gw2h7y2h7tg2fhqotaqjucnbc24deqo72b6mkl2egezxhvy"),
)


@pytest.fixture
def client(mocker):
    client = mocker.patch("ddw.bluesky.Client").return_value
    client.login.return_value = mocker.Mock(did="did:plc:me")
    client.upload_blob.return_value = mocker.Mock(blob=BLOB)
    client.get_author_feed.return_value = mocker.Mock(feed=[])
    return client


CARD = LinkCard(
    url="https://diddukewin.com/g/20261112-abc123/",
    title="Did Duke Win? Yes",
    description="W 82-75",
    image_png=b"png-bytes",
)


class TestPostSkeet:
    def test_with_card_attaches_external_embed_with_thumbnail(self, client):
        Skeeter("u", "p").post_skeet("YES. 82-75", CARD)

        client.upload_blob.assert_called_once_with(b"png-bytes")
        embed = client.send_post.call_args.kwargs["embed"]
        assert embed.external.uri == CARD.url
        assert embed.external.title == "Did Duke Win? Yes"
        assert embed.external.description == "W 82-75"
        assert embed.external.thumb == BLOB

    def test_link_facet_points_at_the_card_url(self, client):
        Skeeter("u", "p").post_skeet("YES. 82-75", CARD)

        text_builder = client.send_post.call_args.kwargs["text"]
        assert text_builder.build_facets()[0].features[0].uri == CARD.url

    def test_without_card_posts_text_only_to_homepage(self, client):
        Skeeter("u", "p").post_skeet("YES. 82-75")

        kwargs = client.send_post.call_args.kwargs
        assert kwargs["embed"] is None
        client.upload_blob.assert_not_called()
        assert (
            kwargs["text"].build_facets()[0].features[0].uri == "https://diddukewin.com"
        )

    def test_image_upload_failure_still_posts(self, client):
        client.upload_blob.side_effect = RuntimeError("boom")

        Skeeter("u", "p").post_skeet("YES. 82-75", CARD)

        assert client.send_post.call_args.kwargs["embed"] is None
