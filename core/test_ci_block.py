from django.test import TestCase


class DeliberateFailureTest(TestCase):
    def test_ci_must_block_this(self):
        self.assertTrue(False, 'Deliberate failure to prove CI blocks the merge')
