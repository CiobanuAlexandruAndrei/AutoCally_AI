from flask import Blueprint, request, jsonify, send_file
from flask_login import current_user
from .models import BaseKnowledge, TaskStatusBaseKnowledge, Assistant, BaseKnowledgeFile
from ..extensions import db
from . import base_knowledge
from ..security.routes import auth
import shutil
from pathlib import Path
from ..config import BASE_DIR
from werkzeug.utils import secure_filename
import os

@base_knowledge.route('/', methods=['GET'])
@auth.login_required
def get_base_knowledge():
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.filter_by(profile_id=current_profile.id).all()
    
    def get_folder_size(folder_path):
        total_size = 0
        folder = Path(BASE_DIR / folder_path)
        if folder.exists():
            for path in folder.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
        return total_size
    
    print(r"-" * 20)
    for bk in base_knowledge:
        print(bk.assistants)
    print(r"-" * 20)

    return jsonify([{
        'id': bk.id,
        'name': bk.name,
        'description': bk.description,
        'assistant_ids': [a.id for a in bk.assistants],
        'folder_path': bk.folder_path,
        'created_at': bk.created_at,
        'updated_at': bk.updated_at,
        'last_loaded': bk.last_loaded,
        'document_count': len(bk.files),
        'needs_reload': bk.needs_reload,
        'total_size': get_folder_size(bk.folder_path)
    } for bk in base_knowledge])

@base_knowledge.route('/<int:base_knowledge_id>', methods=['GET'])
@auth.login_required
def get_base_knowledge_by_id(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
        
    return jsonify({
        'id': base_knowledge.id,
        'name': base_knowledge.name,
        'description': base_knowledge.description,
        'assistant_ids': [a.id for a in base_knowledge.assistants],
        'folder_path': base_knowledge.folder_path,
        'created_at': base_knowledge.created_at,
        'updated_at': base_knowledge.updated_at
    })
    
@base_knowledge.route('/tasks/<task_id>', methods=['GET'])
@auth.login_required
def get_task_status(task_id):
    task_status = TaskStatusBaseKnowledge.query.filter_by(task_id=task_id).first()
    if not task_status:
        return jsonify({'error': 'Task not found'}), 404
        
    return jsonify({
        'task_id': task_status.task_id,
        'status': task_status.status,
        'progress': task_status.progress,
        'total_steps': task_status.total_steps,
        'progress_percentage': (task_status.progress / task_status.total_steps) * 100 if task_status.total_steps > 0 else 0,
        'status_message': task_status.status_message,
        'result': task_status.result,
        'error': task_status.error,
        'created_at': task_status.created_at,
        'updated_at': task_status.updated_at
    })

@base_knowledge.route('/<int:base_knowledge_id>/process', methods=['POST'])
@auth.login_required
def start_processing(base_knowledge_id):
    from ..tasks import process_base_knowledge
    
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Reset the needs_reload flag when starting processing
    base_knowledge.needs_reload = False
    db.session.commit()
    
    task = process_base_knowledge.apply_async(args=[base_knowledge_id])
    return jsonify({
        'task_id': task.id,
        'status': 'PENDING'
    }) 

@base_knowledge.route('/', methods=['POST'])
@auth.login_required
def create_base_knowledge():
    data = request.get_json()
    current_user = auth.current_user()
    current_profile = current_user.profile

    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400

    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400

    # Get list of assistant IDs
    assistant_ids = data.get('assistant_ids', [])

    # Verify all assistants exist and belong to the user
    assistants = Assistant.query.filter(
        Assistant.id.in_(assistant_ids),
        Assistant.profile_id == current_profile.id
    ).all()

    if len(assistants) != len(assistant_ids):
        return jsonify({'error': 'One or more invalid assistant IDs'}), 400

    folder_name = f"base_knowledge_{current_profile.id}_{name.lower().replace(' ', '_')}"
    folder_path = str(Path('files') / folder_name)
    full_folder_path = BASE_DIR / folder_path
    full_folder_path.mkdir(exist_ok=True)

    new_base_knowledge = BaseKnowledge(
        name=name,
        description=data.get('description'),
        profile_id=current_profile.id,
        folder_path=folder_path,
        assistants=assistants
    )

    try:
        db.session.add(new_base_knowledge)
        db.session.commit()

        return jsonify({
            'message': 'Base knowledge created successfully',
            'base_knowledge': {
                'id': new_base_knowledge.id,
                'name': new_base_knowledge.name,
                'description': new_base_knowledge.description,
                'assistant_ids': [a.id for a in new_base_knowledge.assistants],
                'folder_path': new_base_knowledge.folder_path,
                'created_at': new_base_knowledge.created_at,
                'updated_at': new_base_knowledge.updated_at
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/files', methods=['GET'])
@auth.login_required
def get_base_knowledge_files(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    files = base_knowledge.files
    
    return jsonify([{
        'id': file.id,
        'name': file.name,
        'file_path': file.file_path,
        'file_type': file.file_type,
        'file_size': file.file_size,
        'created_at': file.created_at,
        'updated_at': file.updated_at
    } for file in files])

@base_knowledge.route('/<int:base_knowledge_id>/assistants', methods=['POST'])
@auth.login_required
def add_assistant_to_base_knowledge(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.get_json()
    assistant_id = data.get('assistant_id')
    
    if not assistant_id:
        return jsonify({'error': 'Assistant ID is required'}), 400
    
    assistant = Assistant.query.get_or_404(assistant_id)
    
    if assistant.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access to assistant'}), 403
    
    if assistant in base_knowledge.assistants:
        return jsonify({'error': 'Assistant already added to this base knowledge'}), 400
    
    base_knowledge.assistants.append(assistant)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Assistant added successfully',
            'assistant_ids': [a.id for a in base_knowledge.assistants]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/assistants/<int:assistant_id>', methods=['DELETE'])
@auth.login_required
def remove_assistant_from_base_knowledge(base_knowledge_id, assistant_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    assistant = Assistant.query.get_or_404(assistant_id)
    
    if assistant not in base_knowledge.assistants:
        return jsonify({'error': 'Assistant not found in this base knowledge'}), 404
    
    base_knowledge.assistants.remove(assistant)
    
    try:
        db.session.commit()
        return jsonify({
            'message': 'Assistant removed successfully',
            'assistant_ids': [a.id for a in base_knowledge.assistants]
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>', methods=['PUT'])
@auth.login_required
def update_base_knowledge(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.get_json()
    
    if 'name' in data:
        base_knowledge.name = data['name']
    if 'description' in data:
        base_knowledge.description = data['description']
    
    try:
        db.session.commit()
        return jsonify({
            'id': base_knowledge.id,
            'name': base_knowledge.name,
            'description': base_knowledge.description,
            'assistant_ids': [a.id for a in base_knowledge.assistants],
            'folder_path': base_knowledge.folder_path,
            'created_at': base_knowledge.created_at,
            'updated_at': base_knowledge.updated_at
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>', methods=['DELETE'])
@auth.login_required
def delete_base_knowledge(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    try:
        # Store folder path before deleting database records
        folder_path = Path(BASE_DIR / base_knowledge.folder_path)
        files_path = folder_path / 'files'
        chroma_path = folder_path / 'chroma_db'
        
        for file in base_knowledge.files:
            db.session.delete(file)
        
      
        TaskStatusBaseKnowledge.query.filter_by(base_knowledge_id=base_knowledge_id).delete()
        
        base_knowledge.assistants = []
        

        db.session.delete(base_knowledge)
        db.session.commit()

        
        if files_path.exists():
            shutil.rmtree(files_path)
            print(f"Successfully deleted files directory: {files_path}")
            
       
        if chroma_path.exists():
            shutil.rmtree(chroma_path)
            print(f"Successfully deleted chroma_db directory: {chroma_path}")
            
       
        if folder_path.exists():
            if not any(folder_path.iterdir()):  
                folder_path.rmdir()  
                print(f"Successfully deleted empty base folder: {folder_path}")
        
        return jsonify({'message': 'Base knowledge deleted successfully'})
        
    except Exception as e:
        print(f"Error in delete_base_knowledge: {str(e)}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/files', methods=['POST'])
@auth.login_required
def upload_file(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
        
    if file:
        filename = secure_filename(file.filename)
 
        files_dir = Path(BASE_DIR / base_knowledge.folder_path / 'files')
        files_dir.mkdir(exist_ok=True)
        
        file_path = files_dir / filename
        file.save(str(file_path))
        
        file_size = os.path.getsize(str(file_path))
        file_type = os.path.splitext(filename)[1][1:] # Get extension without dot
        
        new_file = BaseKnowledgeFile(
            name=filename,
            description=request.form.get('description', ''),
            base_knowledge_id=base_knowledge.id,
            file_path=str(Path('files') / filename),
            file_type=file_type,
            file_size=file_size
        )
        
        try:
            db.session.add(new_file)
            base_knowledge.needs_reload = True  # Set the flag
            db.session.commit()
            
            return jsonify({
                'message': 'File uploaded successfully',
                'file': {
                    'id': new_file.id,
                    'name': new_file.name,
                    'description': new_file.description,
                    'file_path': new_file.file_path,
                    'file_type': new_file.file_type,
                    'file_size': new_file.file_size,
                    'created_at': new_file.created_at,
                    'updated_at': new_file.updated_at
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            # Delete the file if database operation fails
            if file_path.exists():
                file_path.unlink()
            return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/text', methods=['POST'])
@auth.login_required
def create_text_file(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    data = request.get_json()
    if not data or 'title' not in data or 'content' not in data:
        return jsonify({'error': 'Title and content are required'}), 400
        

    filename = secure_filename(data['title'])
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    files_dir = Path(BASE_DIR / base_knowledge.folder_path / 'files')
    files_dir.mkdir(exist_ok=True)
    
    file_path = files_dir / filename
    
    try:
      
        with open(str(file_path), 'w', encoding='utf-8') as f:
            f.write(data['content'])
        
        file_size = os.path.getsize(str(file_path))
        
        new_file = BaseKnowledgeFile(
            name=filename,
            description=data.get('description', ''),
            base_knowledge_id=base_knowledge.id,
            file_path=str(Path('files') / filename),
            file_type='txt',
            file_size=file_size
        )
        
        db.session.add(new_file)
        base_knowledge.needs_reload = True
        db.session.commit()
        
        return jsonify({
            'message': 'Text file created successfully',
            'file': {
                'id': new_file.id,
                'name': new_file.name,
                'description': new_file.description,
                'file_path': new_file.file_path,
                'file_type': new_file.file_type,
                'file_size': new_file.file_size,
                'created_at': new_file.created_at,
                'updated_at': new_file.updated_at
            }
        }), 201
        
    except Exception as e:
        # Delete the file if database operation fails
        if file_path.exists():
            file_path.unlink()
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/files/<int:file_id>', methods=['DELETE'])
@auth.login_required
def remove_file(base_knowledge_id, file_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    file = BaseKnowledgeFile.query.get_or_404(file_id)
    
    if file.base_knowledge_id != base_knowledge_id:
        return jsonify({'error': 'File does not belong to this base knowledge'}), 400
    
    try:
        # Delete the physical file
        file_path = Path(BASE_DIR / base_knowledge.folder_path / 'files' / file.name)
        if file_path.exists():
            file_path.unlink()
        
        # Delete the database record
        db.session.delete(file)
        base_knowledge.needs_reload = True
        db.session.commit()
        
        return jsonify({'message': 'File deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/files/<int:file_id>/content', methods=['GET'])
@auth.login_required
def get_file_content(base_knowledge_id, file_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    file = BaseKnowledgeFile.query.get_or_404(file_id)
    
    if file.base_knowledge_id != base_knowledge_id:
        return jsonify({'error': 'File does not belong to this base knowledge'}), 400
        
    if file.file_type != 'txt':
        return jsonify({'error': 'File is not a text file'}), 400
    
    file_path = Path(BASE_DIR / base_knowledge.folder_path / 'files' / file.name)
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return jsonify({
            'content': content,
            'file': {
                'id': file.id,
                'name': file.name,
                'description': file.description,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'created_at': file.created_at,
                'updated_at': file.updated_at
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@base_knowledge.route('/<int:base_knowledge_id>/files/<int:file_id>/download', methods=['GET'])
@auth.login_required
def download_file(base_knowledge_id, file_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    file = BaseKnowledgeFile.query.get_or_404(file_id)
    
    if file.base_knowledge_id != base_knowledge_id:
        return jsonify({'error': 'File does not belong to this base knowledge'}), 400
    
    file_path = Path(BASE_DIR / base_knowledge.folder_path / 'files' / file.name)
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
        
    return send_file(
        file_path,
        as_attachment=True,
        download_name=file.name
    )

@base_knowledge.route('/<int:base_knowledge_id>/files/<int:file_id>', methods=['PUT'])
@auth.login_required
def update_text_file(base_knowledge_id, file_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    file = BaseKnowledgeFile.query.get_or_404(file_id)
    
    if file.base_knowledge_id != base_knowledge_id:
        return jsonify({'error': 'File does not belong to this base knowledge'}), 400
        
    if file.file_type != 'txt':
        return jsonify({'error': 'File is not a text file'}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
        
    try:
        old_file_path = Path(BASE_DIR / base_knowledge.folder_path / 'files' / file.name)
        
        # Handle title/name change
        if 'title' in data:
            new_filename = secure_filename(data['title'])
            if not new_filename.endswith('.txt'):
                new_filename += '.txt'
                
            new_file_path = Path(BASE_DIR / base_knowledge.folder_path / 'files' / new_filename)
            
            # If name changed, remove old file
            if new_filename != file.name:
                if old_file_path.exists():
                    old_file_path.unlink()
                file.name = new_filename
                file_path = new_file_path
            else:
                file_path = old_file_path
        else:
            file_path = old_file_path
            
        # Update content if provided
        if 'content' in data:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(data['content'])
            file.file_size = os.path.getsize(str(file_path))
            
        # Update description if provided
        if 'description' in data:
            file.description = data['description']
            
        base_knowledge.needs_reload = True
        db.session.commit()
        
        return jsonify({
            'message': 'File updated successfully',
            'file': {
                'id': file.id,
                'name': file.name,
                'description': file.description,
                'file_path': file.file_path,
                'file_type': file.file_type,
                'file_size': file.file_size,
                'created_at': file.created_at,
                'updated_at': file.updated_at
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400

@base_knowledge.route('/<int:base_knowledge_id>/tasks/last', methods=['GET'])
@auth.login_required
def get_last_task_status(base_knowledge_id):
    current_user = auth.current_user()
    current_profile = current_user.profile
    
    if not current_profile:
        return jsonify({'error': 'No profile found for user'}), 400
        
    base_knowledge = BaseKnowledge.query.get_or_404(base_knowledge_id)
    
    if base_knowledge.profile_id != current_profile.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    task_status = TaskStatusBaseKnowledge.query\
        .filter_by(base_knowledge_id=base_knowledge_id)\
        .order_by(TaskStatusBaseKnowledge.created_at.desc())\
        .first()
    
    if not task_status:
        return jsonify({'error': 'No tasks found for this base knowledge'}), 404
        
    return jsonify({
        'task_id': task_status.task_id,
        'status': task_status.status,
        'progress': task_status.progress,
        'total_steps': task_status.total_steps,
        'progress_percentage': (task_status.progress / task_status.total_steps) * 100 if task_status.total_steps > 0 else 0,
        'status_message': task_status.status_message,
        'result': task_status.result,
        'error': task_status.error,
        'created_at': task_status.created_at,
        'updated_at': task_status.updated_at
    })


