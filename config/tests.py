from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from .models import Evaluation, GoogleIdentity


class SiteSearchTests(TestCase):
    def test_search_finds_pages_without_accent_sensitive_matching(self):
        response = self.client.get('/buscar/', {'q': 'avaliacoes'})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Avaliações')
        self.assertContains(response, '/avaliacao.html')

    def test_search_finds_evaluations_and_normalizes_accents(self):
        Evaluation.objects.create(
            category=Evaluation.Category.SERVICE,
            rating=5,
            comment='A comida está ótima e o atendimento foi excelente.',
        )

        response = self.client.get('/buscar/', {'q': 'otima'})

        self.assertContains(response, 'A comida está ótima')
        self.assertContains(response, 'Atendimento')

    def test_search_displays_empty_state_for_unknown_term(self):
        response = self.client.get('/buscar/', {'q': 'palavra-inexistente'})

        self.assertContains(response, 'Nenhum resultado encontrado')

    def test_search_form_is_available_on_public_pages(self):
        for path in (
            '/',
            '/avaliacao.html',
            '/avaliar-pratos.html',
            '/avaliar-atendimento.html',
            '/avaliar-estabelecimento.html',
            '/contato.html',
            '/serviço.html',
            '/entrar.html',
            '/cadastrar.html',
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'action="/buscar/"')
                self.assertContains(response, 'name="q"')


class AccountFlowTests(TestCase):
    def test_login_page_offers_google_sign_in(self):
        response = self.client.get('/entrar/')

        self.assertContains(response, 'class="g_id_signin"')
        self.assertContains(response, 'data-text="continue_with"')
        self.assertContains(response, "fetch('/auth/google/'")

    def test_registration_creates_account_and_reports_success(self):
        response = self.client.post('/cadastrar/', {
            'nome': 'Ana Silva',
            'usuario': 'ana-silva',
            'senha': 'Forte!Senha-9284',
        }, follow=True)

        user = get_user_model().objects.get(username='ana-silva')
        self.assertTrue(user.check_password('Forte!Senha-9284'))
        self.assertContains(response, 'Cadastro concluído')

    def test_registration_rejects_duplicate_username(self):
        get_user_model().objects.create_user(
            username='ana-silva',
            password='Forte!Senha-9284',
        )

        response = self.client.post('/cadastrar/', {
            'nome': 'Ana Silva',
            'usuario': 'ana-silva',
            'senha': 'Outra!Senha-9284',
        })

        self.assertContains(response, 'já está em uso')
        self.assertEqual(get_user_model().objects.filter(username='ana-silva').count(), 1)

    def test_login_and_logout_control_dashboard_access(self):
        get_user_model().objects.create_user(
            username='ana-silva',
            password='Forte!Senha-9284',
        )

        response = self.client.post('/entrar/', {
            'usuario': 'ana-silva',
            'senha': 'Forte!Senha-9284',
        })
        self.assertRedirects(response, '/dashboard.html')
        self.assertEqual(self.client.get('/dashboard.html').status_code, 200)
        self.assertEqual(self.client.get('/dashboard-avaliacoes.html').status_code, 200)

        response = self.client.post('/sair/')
        self.assertRedirects(response, '/')
        self.assertRedirects(self.client.get('/dashboard.html'), '/entrar/?next=/dashboard.html')

    def test_invalid_login_does_not_open_dashboard(self):
        response = self.client.post('/entrar/', {
            'usuario': 'nao-existe',
            'senha': 'Forte!Senha-9284',
        })

        self.assertContains(response, 'Usuário ou senha inválidos')
        self.assertRedirects(self.client.get('/dashboard.html'), '/entrar/?next=/dashboard.html')

    def test_login_form_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/entrar/')

        response = client.post('/entrar/', {
            'usuario': 'ana-silva',
            'senha': 'Forte!Senha-9284',
        })

        self.assertEqual(response.status_code, 403)


class GoogleLoginTests(TestCase):
    def test_google_login_start_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            '/auth/google/',
            {'credential': 'google-id-token'},
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_google_login_button_uses_the_provided_client_id(self):
        response = self.client.get('/entrar/')

        self.assertContains(response, '953718056226-pqkq5cpoalb2gkocjenigngm33hu3nte.apps.googleusercontent.com')
        self.assertContains(response, 'https://accounts.google.com/gsi/client')
        self.assertContains(response, 'data-callback="handleGoogleCredential"')
        self.assertContains(response, 'data-nonce=')

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='test-client-id')
    def test_google_login_verifies_id_token_and_creates_account(self):
        from unittest.mock import patch

        self.client.get('/entrar/')
        nonce = self.client.session['google_login_nonce']
        with patch('google.oauth2.id_token.verify_oauth2_token') as verify_token:
            verify_token.return_value = {
                'sub': 'google-subject-123',
                'email': 'google-user@example.com',
                'email_verified': True,
                'name': 'Google User',
                'nonce': nonce,
            }
            response = self.client.post(
                '/auth/google/',
                {'credential': 'signed-google-id-token'},
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'redirect_url': '/dashboard.html'})
        user = get_user_model().objects.get(email='google-user@example.com')
        self.assertEqual(user.first_name, 'Google')
        self.assertEqual(user.last_name, 'User')
        self.assertFalse(user.has_usable_password())
        self.assertEqual(GoogleIdentity.objects.get(user=user).subject, 'google-subject-123')
        self.assertEqual(self.client.get('/dashboard.html').status_code, 200)
        verify_token.assert_called_once()
        self.assertEqual(verify_token.call_args.kwargs['audience'], 'test-client-id')

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='test-client-id')
    def test_google_login_reuses_existing_google_identity(self):
        from unittest.mock import patch

        user = get_user_model().objects.create_user(
            username='existing-google-user',
            password=None,
        )
        GoogleIdentity.objects.create(user=user, subject='google-subject-123')
        self.client.get('/entrar/')
        nonce = self.client.session['google_login_nonce']
        with patch('google.oauth2.id_token.verify_oauth2_token', return_value={
            'sub': 'google-subject-123',
            'email': 'updated@example.com',
            'email_verified': True,
            'nonce': nonce,
        }):
            response = self.client.post(
                '/auth/google/',
                {'credential': 'signed-google-id-token'},
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'redirect_url': '/dashboard.html'})
        self.assertEqual(get_user_model().objects.count(), 1)
        self.assertEqual(GoogleIdentity.objects.count(), 1)
        self.assertEqual(user.email, '')

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='test-client-id')
    def test_google_login_rejects_invalid_token(self):
        from unittest.mock import patch

        with patch('google.oauth2.id_token.verify_oauth2_token', side_effect=ValueError):
            response = self.client.post(
                '/auth/google/',
                {'credential': 'invalid-token'},
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(get_user_model().objects.count(), 0)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='test-client-id')
    def test_google_login_rejects_unverified_email(self):
        from unittest.mock import patch

        self.client.get('/entrar/')
        with patch('google.oauth2.id_token.verify_oauth2_token', return_value={
            'sub': 'google-subject-123',
            'email': 'google-user@example.com',
            'email_verified': False,
            'nonce': self.client.session['google_login_nonce'],
        }):
            response = self.client.post(
                '/auth/google/',
                {'credential': 'signed-google-id-token'},
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(get_user_model().objects.count(), 0)

    @override_settings(GOOGLE_OAUTH_CLIENT_ID='test-client-id')
    def test_google_login_rejects_token_with_mismatched_nonce(self):
        from unittest.mock import patch

        self.client.get('/entrar/')
        with patch('google.oauth2.id_token.verify_oauth2_token', return_value={
            'sub': 'google-subject-123',
            'email': 'google-user@example.com',
            'email_verified': True,
            'nonce': 'different-nonce',
        }):
            response = self.client.post(
                '/auth/google/',
                {'credential': 'signed-google-id-token'},
                content_type='application/json',
            )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(get_user_model().objects.count(), 0)


class EvaluationApiTests(TestCase):
    def test_dashboard_summary_uses_real_evaluation_data(self):
        Evaluation.objects.create(
            category=Evaluation.Category.DISHES,
            rating=4,
            dish_id='temaki-salmao',
            dish_name='Temaki de Salmão',
            comment='Muito bom.',
        )

        response = self.client.get('/api/avaliacoes/')
        data = response.json()

        self.assertEqual(data['total'], 1)
        self.assertEqual(data['media_geral'], 4)
        self.assertEqual(data['distribuicao_notas']['pratos']['4'], 1)
        self.assertEqual(data['produtos_mais_avaliados'][0]['dish_name'], 'Temaki de Salmão')
        self.assertEqual(data['ultimas_avaliacoes'][0]['comentario'], 'Muito bom.')

    def test_evaluation_submission_updates_searchable_review_data(self):
        response = self.client.post('/api/avaliacoes/', {
            'category': 'atendimento',
            'rating': 5,
            'comment': 'Atendimento excelente e rápido.',
        }, content_type='application/json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Evaluation.objects.count(), 1)
        self.assertContains(self.client.get('/buscar/', {'q': 'rapido'}), 'excelente e rápido')

    def test_evaluation_api_rejects_invalid_rating(self):
        response = self.client.post('/api/avaliacoes/', {
            'category': 'atendimento',
            'rating': 6,
        }, content_type='application/json')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Evaluation.objects.count(), 0)
