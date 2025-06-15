import os
import time
import random
import logging
import json
import base64
import re
import magic
from io import BytesIO
from typing import Dict, List, Optional, Tuple

from django.views import View
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from django.conf import settings
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models import Count
from django.middleware.csrf import get_token
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from pylatexenc.latex2text import LatexNodes2Text
import sympy
from sympy import latex
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
from openai import OpenAI
from pylatexenc.latex2text import LatexNodes2Text

from .models import MathProblem
from .serializers import MathProblemSerializer

logger = logging.getLogger(__name__)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.DEEPSEEK_API_KEY
)

# Rest of your code...


@login_required
def user_math_problems(request):
    problems = MathProblem.objects.filter(user=request.user).order_by('-created_at')
    
    data = []
    for problem in problems:
        data.append({
            'id': problem.id,
            'input_type': problem.input_type,
            'extracted_problem': problem.extracted_problem,
            'solution': problem.solution,
            'explanation': problem.explanation,
            'processing_time': problem.processing_time,
            'created_at': problem.created_at.isoformat(),
        })
    
    return JsonResponse(data, safe=False)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json

@csrf_exempt
def api_login(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'Nom d\'utilisateur et mot de passe requis'
                }, status=400)
            
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({
                    'status': 'success',
                    'message': 'Connexion réussie',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                })
            return JsonResponse({
                'status': 'error', 
                'message': 'Identifiants invalides'
            }, status=401)
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error', 
                'message': 'Données JSON invalides'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': str(e)
            }, status=500)
    return JsonResponse({
        'status': 'error', 
        'message': 'Méthode non autorisée'
    }, status=405)

@csrf_exempt
@login_required
def api_profile(request):
    if request.method == 'GET':
        user = request.user
        return JsonResponse({
            'status': 'success',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            }
        })
    return JsonResponse({
        'status': 'error', 
        'message': 'Méthode non autorisée'
    }, status=405)

@csrf_exempt
@login_required
def api_logout(request):
    if request.method == 'POST':
        logout(request)
        return JsonResponse({
            'status': 'success', 
            'message': 'Déconnexion réussie'
        })
    return JsonResponse({
        'status': 'error', 
        'message': 'Méthode non autorisée'
    }, status=405)

@csrf_exempt
def api_register(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            
            # Validation des champs obligatoires
            if not username or not email or not password:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Tous les champs obligatoires doivent être remplis'
                }, status=400)
                
            # Vérification de l'unicité du username
            if User.objects.filter(username=username).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Ce nom d\'utilisateur est déjà pris'
                }, status=400)
            
            # Vérification de l'unicité de l'email
            if User.objects.filter(email=email).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'Cet email est déjà utilisé'
                }, status=400)
            
            # Création de l'utilisateur
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Authentification automatique après inscription
            login(request, user)
            
            return JsonResponse({
                'status': 'success',
                'message': 'Inscription réussie',
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Données JSON invalides'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur serveur: {str(e)}'
            }, status=500)
    return JsonResponse({
        'status': 'error',
        'message': 'Méthode non autorisée'
    }, status=405)


    

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('math_solver')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('math_solver')


def extract_text_from_file(file, file_type):
    """Extrait le texte d'un fichier selon son type (TEXT, IMAGE, PDF)"""
    if file_type == 'TEXT':
        return file.read().decode('utf-8')
    
    elif file_type == 'IMAGE':
        image = Image.open(BytesIO(file.read()))
        return pytesseract.image_to_string(image)
    
    elif file_type == 'PDF':
        images = convert_from_bytes(file.read())
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
        return text.strip()
    
    return ""

def generate_prompt(problem_text, language):
    """Génère le prompt adapté selon la langue"""
    if language == 'en':
        return (
            f"Please solve this math problem with detailed step-by-step explanations:\n\n"
            f"{problem_text}\n\n"
            f"Provide the solution in clear English with all reasoning steps."
        )
    else:  # français par défaut
        return (
            f"Résolvez ce problème mathématique avec des explications détaillées étape par étape :\n\n"
            f"{problem_text}\n\n"
            f"Fournissez la solution en français clair avec toutes les étapes de raisonnement."
        )

def solve_math_problem(problem_text, language='fr'):
    """Utilise l'API DeepSeek pour résoudre le problème"""
    prompt = generate_prompt(problem_text, language)
    
    response = client.chat.completions.create(
        model="deepseek/deepseek-r1-0528-qwen3-8b:free",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content

def cleanup_old_entries(user):
    """Supprime les anciennes entrées au-delà de la limite de 20"""
    if user.is_authenticated:import re


def extract_text_from_file(file, file_type):
    """Extrait le texte d'un fichier avec une meilleure gestion des fractions"""
    try:
        if file_type == 'TEXT':
            content = file.read().decode('utf-8')
            return clean_extracted_text(content)
        
        elif file_type == 'IMAGE':
            # Configuration spécifique pour les mathématiques
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ(){}[]+-=<>/\\^_.,:;!?%&*$#'
            image = Image.open(BytesIO(file.read()))
            text = pytesseract.image_to_string(image, config=custom_config)
            return clean_extracted_text(text)
        
        elif file_type == 'PDF':
            images = convert_from_bytes(file.read(), dpi=300)  # Meilleure résolution
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image) + "\n"
            return clean_extracted_text(text.strip())
        
        return ""
    except Exception as e:
        raise Exception(f"Erreur d'extraction: {str(e)}")

def clean_extracted_text(text):
    """Nettoie le texte extrait et améliore la lisibilité des fractions"""
    # Normaliser les fractions
    text = re.sub(r'(\d+)\s*/\s*(\d+)', r'\\frac{\1}{\2}', text)
    # Corriger d'autres patterns mathématiques courants
    text = re.sub(r'(\d+)\s*-\s*(\d+)', r'\1-\2', text)  # Éviter les espaces dans les négatifs
    return text

def generate_prompt(problem_text, language):
    """Génère un prompt concis et efficace"""
    problem_text = convert_latex_to_unicode(problem_text)
    
    if language == 'en':
        return (
            f"Solve this math problem showing key steps only:\n"
            f"Problem: {problem_text}\n"
            f"Provide the solution in English with essential steps only."
        )
    else:  # français par défaut
        return (
            f"Résolvez ce problème mathématique en montrant les étapes clés seulement :\n"
            f"Problème: {problem_text}\n"
            f"Fournissez la solution en français avec les étapes essentielles seulement."
        )

def convert_latex_to_unicode(text):
    """Convertit les expressions LaTeX en Unicode lisible"""
    try:
        return LatexNodes2Text().latex_to_text(text)
    except:
        return text

def solve_math_problem(problem_text, language='fr'):
    """Version améliorée avec gestion des erreurs"""
    prompt = generate_prompt(problem_text, language)
    
    try:
        response = client.chat.completions.create(
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
            messages=[
                {"role": "system", "content": "You are a concise math assistant. Provide step-by-step solutions without unnecessary explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3  # Réduit la verbosité
        )
        
        solution = response.choices[0].message.content
        return post_process_solution(solution)
    except Exception as e:
        raise Exception(f"API Error: {str(e)}")

def post_process_solution(solution):
    """Nettoie la solution pour enlever les bavardages"""
    # Supprime les phrases d'introduction génériques
    solution = re.sub(r'^((Voici|Here is).*?\n)', '', solution, flags=re.IGNORECASE)
    # Supprime les conclusions génériques
    solution = re.sub(r'(\n.*?(Donc|Therefore).*$)', '', solution, flags=re.IGNORECASE)
    """user_problems = MathProblem.objects.filter(user=user)
        if user_problems.count() > 20:
            ids_to_delete = user_problems.order_by('-created_at')[20:].values_list('id', flat=True)
            MathProblem.objects.filter(id__in=ids_to_delete).delete()"""
    return solution.strip()
        


@csrf_exempt
def api_solve_math_problem(request):
    """Vue API pour résoudre les problèmes mathématiques"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
    
    start_time = time.time()
    
    try:
        # Vérifier si la requête est multipart/form-data pour les fichiers
        if 'multipart/form-data' in request.content_type:
            file = request.FILES.get('file')
            text_input = request.POST.get('text', '')
            language = request.POST.get('language', 'fr')
        else:
            # Pour les requêtes JSON
            data = json.loads(request.body)
            file = None
            text_input = data.get('text', '')
            language = data.get('language', 'fr')
            
            # Gérer le fichier encodé en base64 si présent
            if 'file' in data and 'file_name' in data:
                file_data = data['file']
                file_name = data['file_name']
                file = ContentFile(base64.b64decode(file_data), name=file_name)
        
        if not file and not text_input:
            return JsonResponse(
                {'error': 'Aucune entrée fournie. Veuillez fournir un texte ou un fichier.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Traitement du fichier
        problem_text = ''
        file_type = None
        
        if file:
            try:
                # Déterminer le type de fichier
                mime = magic.from_buffer(file.read(1024), mime=True)
                file.seek(0)
                
                if mime.startswith('image/'):
                    file_type = 'IMAGE'
                elif mime == 'application/pdf':
                    file_type = 'PDF'
                else:
                    try:
                        # Essayer de lire comme texte
                        content = file.read().decode('utf-8')
                        file_type = 'TEXT'
                        file = ContentFile(content.encode('utf-8'))
                    except:
                        return JsonResponse(
                            {'error': 'Format de fichier non supporté. Formats acceptés: texte, PDF, images.'},
                            status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
                        )
                
                # Extraire le texte du fichier
                problem_text = extract_text_from_file(file, file_type)
                
            except Exception as e:
                logger.error(f"Erreur d'extraction du fichier: {str(e)}")
                return JsonResponse(
                    {'error': f"Erreur lors du traitement du fichier: {str(e)}"},
                    status=status.HTTP_422_UNPROCESSABLE_ENTITY
                )
        else:
            problem_text = text_input
            file_type = 'TEXT'
        
        # Résolution du problème mathématique
        try:
            solution = solve_math_problem(problem_text, language)
        except Exception as e:
            logger.error(f"Erreur de résolution: {str(e)}")
            return JsonResponse(
                {'error': f"Erreur lors de la résolution du problème: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        processing_time = time.time() - start_time
        
        # Sauvegarde dans l'historique si utilisateur authentifié
        if request.user.is_authenticated:
            try:
                cleanup_old_entries(request.user)
                
                # Sauvegarder le contenu original
                original_content = None
                if file:
                    file.seek(0)
                    original_content = file.read()
                    file.seek(0)
                else:
                    original_content = text_input.encode('utf-8')
                
                MathProblem.objects.create(
                    user=request.user,
                    input_type=file_type,
                    original_input=original_content,
                    extracted_problem=problem_text,
                    solution=solution,
                    processing_time=processing_time
                )
            except Exception as e:
                logger.error(f"Erreur de sauvegarde dans l'historique: {str(e)}")
                # On continue même si l'historique échoue
        
        # Formater la réponse
        response_data = {
            'problem': problem_text,
            'solution': solution,
            'processing_time': round(processing_time, 2),
            'language': language,
            'timestamp': timezone.now().isoformat()
        }
        
        return JsonResponse(response_data, status=status.HTTP_200_OK)
    
    except json.JSONDecodeError:
        return JsonResponse(
            {'error': 'Format de données invalide. Envoyez du JSON ou utilisez form-data.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        logger.error(f"Erreur inattendue: {str(e)}")
        return JsonResponse(
            {'error': 'Une erreur inattendue est survenue.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    

def math_solver_view(request):
    """Vue locale pour l'interface utilisateur avec même logique que l'API"""
    context = {'history': []}
    
    if request.user.is_authenticated:
        context['history'] = MathProblem.objects.filter(user=request.user).order_by('-created_at')[:20]
    
    if request.method == 'POST':
        start_time = time.time()
        
        try:
            # Gestion des fichiers et texte d'entrée
            file = request.FILES.get('file')
            text_input = request.POST.get('text', '')
            language = request.POST.get('language', 'fr')
            
            if not file and not text_input:
                context['error'] = 'Aucune entrée fournie. Veuillez fournir un texte ou un fichier.'
                return render(request, 'math_solver.html', context)
            
            # Traitement du fichier
            problem_text = ''
            file_type = None
            
            if file:
                try:
                    mime = magic.from_buffer(file.read(1024), mime=True)
                    file.seek(0)
                    
                    if mime.startswith('image/'):
                        file_type = 'IMAGE'
                    elif mime == 'application/pdf':
                        file_type = 'PDF'
                    else:
                        try:
                            content = file.read().decode('utf-8')
                            file_type = 'TEXT'
                            file = ContentFile(content.encode('utf-8'))
                        except:
                            context['error'] = 'Format de fichier non supporté. Formats acceptés: texte, PDF, images.'
                            return render(request, 'math_solver.html', context)
                    
                    problem_text = extract_text_from_file(file, file_type)
                    
                except Exception as e:
                    logger.error(f"Erreur d'extraction du fichier: {str(e)}")
                    context['error'] = f"Erreur lors du traitement du fichier: {str(e)}"
                    return render(request, 'math_solver.html', context)
            else:
                problem_text = text_input
                file_type = 'TEXT'
            
            # Résolution du problème
            try:
                solution = solve_math_problem(problem_text, language)
            except Exception as e:
                logger.error(f"Erreur de résolution: {str(e)}")
                context['error'] = f"Erreur lors de la résolution du problème: {str(e)}"
                return render(request, 'math_solver.html', context)
            
            processing_time = time.time() - start_time
            
            # Sauvegarde dans l'historique
            try:
                cleanup_old_entries(request.user)
                
                original_content = None
                if file:
                    file.seek(0)
                    original_content = file.read()
                    file.seek(0)
                else:
                    original_content = text_input.encode('utf-8')
                
                MathProblem.objects.create(
                    user=request.user,
                    input_type=file_type,
                    original_input=original_content,
                    extracted_problem=problem_text,
                    solution=solution,
                    processing_time=processing_time
                )
                
                # Mettre à jour l'historique dans le contexte
                context['history'] = MathProblem.objects.filter(user=request.user).order_by('-created_at')[:20]
                
            except Exception as e:
                logger.error(f"Erreur de sauvegarde dans l'historique: {str(e)}")
            
            # Ajouter les résultats au contexte
            context.update({
                'problem': problem_text,
                'solution': solution,
                'processing_time': round(processing_time, 2),
                'language': language,
                'success': True
            })
            
        except Exception as e:
            logger.error(f"Erreur inattendue: {str(e)}")
            context['error'] = 'Une erreur inattendue est survenue.'
    
    return render(request, 'math_solver.html', context)

def cleanup_old_entries(user):
    """Nettoyer les anciennes entrées (limite à 20)"""
    if user.is_authenticated:
        user_problems = MathProblem.objects.filter(user=user)
        if user_problems.count() > 20:
            ids_to_delete = user_problems.order_by('-created_at')[20:].values_list('id', flat=True)
            MathProblem.objects.filter(id__in=ids_to_delete).delete()