"""Password reset regression tests; all database calls are mocked."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
import click
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as core

class PasswordResetTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(core.app.app_context())
        self.enterContext(click.Context(core.reset_demo_passwords))

    def test_only_existing_hashes_are_updated_and_printed_after_commit(self):
        stored={}
        roles={'admin.one@example.com':(1,'ADMIN'),
               'reader.one@example.com':(3,'USER'),
               'guest.one@example.com':(5,'GUEST')}
        connection=Mock()
        def sql(query,args):
            if query.startswith('SELECT u.user_id'):
                uid,role=roles[args[0]]
                return [{'user_id':uid,'role':role}]
            if query.startswith('UPDATE login_credentials'):
                stored[args[1]]=args[0]
                return []
            if query.startswith('SELECT password_hash'):
                return [{'password_hash':stored[args[0]]}]
            self.fail('Unexpected database statement')
        printed=[]
        def echo(value):
            connection.commit.assert_called_once()
            printed.append(value)
        with core.app.app_context(),patch.object(core.sys.stdout,'isatty',return_value=True),patch.object(core,'sql',side_effect=sql),patch.object(core,'db',return_value=connection),patch.object(core.click,'echo',side_effect=echo):
            core.reset_demo_passwords.callback()
        self.assertEqual(set(stored),{1,3,5})
        self.assertEqual(len(printed),4)
        passwords=[]
        for line in printed[1:]:
            email,password=line.split('  ')
            passwords.append(password)
            self.assertTrue(core.check_password_hash(stored[roles[email][0]],password))
            self.assertGreaterEqual(len(password),32)
        self.assertEqual(len(set(passwords)),3)
        connection.rollback.assert_not_called()

    def test_role_mismatch_rolls_back_without_output(self):
        connection=Mock()
        with core.app.app_context(),patch.object(core.sys.stdout,'isatty',return_value=True),patch.object(core,'sql',return_value=[{'user_id':1,'role':'USER'}]) as sql,patch.object(core,'db',return_value=connection),patch.object(core.click,'echo') as echo:
            with self.assertRaises(click.ClickException):core.reset_demo_passwords.callback()
        connection.rollback.assert_called_once()
        connection.commit.assert_not_called()
        echo.assert_not_called()
        self.assertTrue(all(call.args[0].startswith('SELECT') for call in sql.call_args_list))

    def test_output_redirection_is_rejected_before_database_access(self):
        with patch.object(core.sys.stdout,'isatty',return_value=False),patch.object(core,'db') as db,patch.object(core,'sql') as sql:
            with self.assertRaises(click.ClickException):core.reset_demo_passwords.callback()
        db.assert_not_called()
        sql.assert_not_called()

if __name__=='__main__':unittest.main()
