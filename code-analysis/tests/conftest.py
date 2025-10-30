"""Pytest configuration and shared fixtures for Code Analysis tests."""

import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_python_simple(temp_dir) -> Path:
    """Create a simple Python file for testing."""
    file_path = temp_dir / "simple.py"
    file_path.write_text('''
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b
''')
    return file_path


@pytest.fixture
def sample_python_complex(temp_dir) -> Path:
    """Create a complex Python file with classes for testing."""
    file_path = temp_dir / "complex.py"
    file_path.write_text('''
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class User:
    """Represents a user in the system."""
    id: int
    name: str
    email: str

    @property
    def display_name(self) -> str:
        """Get the user's display name."""
        return f"{self.name} <{self.email}>"

    def update_email(self, new_email: str) -> None:
        """Update the user's email address."""
        self.email = new_email


class UserService:
    """Service for managing users."""

    def __init__(self, database):
        self.database = database
        self.cache = {}

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get a user by ID."""
        if user_id in self.cache:
            return self.cache[user_id]

        user = await self.database.fetch_user(user_id)
        if user:
            self.cache[user_id] = user
        return user

    async def create_user(self, name: str, email: str, password: str, role: str,
                         department: str, manager_id: int, settings: dict) -> User:
        """Create a new user with many parameters."""
        # This function has too many parameters
        user = User(id=0, name=name, email=email)
        await self.database.save_user(user)
        return user


def complex_function(x: int, y: int) -> int:
    """A complex function with high cyclomatic complexity."""
    result = 0

    if x > 0:
        if y > 0:
            result = x + y
        elif y < 0:
            result = x - y
        else:
            result = x
    elif x < 0:
        if y > 0:
            result = y - x
        elif y < 0:
            result = -(x + y)
        else:
            result = -x
    else:
        result = y

    for i in range(10):
        if i % 2 == 0:
            result += i
        else:
            result -= i

    return result
''')
    return file_path


@pytest.fixture
def sample_python_code_smells(temp_dir) -> Path:
    """Create a Python file with code smells."""
    file_path = temp_dir / "code_smells.py"
    file_path.write_text('''
# Missing docstring
def no_docstring():
    return "bad"

# Too many parameters
def too_many_params(a, b, c, d, e, f, g):
    return a + b + c + d + e + f + g

class GodClass:
    """A class with too many methods."""

    def method1(self): pass
    def method2(self): pass
    def method3(self): pass
    def method4(self): pass
    def method5(self): pass
    def method6(self): pass
    def method7(self): pass
    def method8(self): pass
    def method9(self): pass
    def method10(self): pass
    def method11(self): pass
    def method12(self): pass
    def method13(self): pass
    def method14(self): pass
    def method15(self): pass
    def method16(self): pass
    def method17(self): pass
    def method18(self): pass
    def method19(self): pass
    def method20(self): pass
    def method21(self): pass
    def method22(self): pass
''')
    return file_path


@pytest.fixture
def sample_javascript(temp_dir) -> Path:
    """Create a JavaScript file for testing."""
    file_path = temp_dir / "sample.js"
    file_path.write_text("""
function calculateTotal(items) {
    return items.reduce((sum, item) => sum + item.price, 0);
}

async function fetchUserData(userId) {
    const response = await fetch(`/api/users/${userId}`);
    return response.json();
}

class UserManager {
    constructor() {
        this.users = new Map();
    }

    addUser(id, name) {
        this.users.set(id, { id, name });
    }

    getUser(id) {
        return this.users.get(id);
    }
}

const processData = (data) => {
    return data.filter(item => item.active)
               .map(item => item.value);
};
""")
    return file_path


@pytest.fixture
def sample_typescript(temp_dir) -> Path:
    """Create a TypeScript file for testing."""
    file_path = temp_dir / "sample.ts"
    file_path.write_text("""
interface User {
    id: number;
    name: string;
    email: string;
}

class UserService {
    private users: Map<number, User> = new Map();

    async getUser(id: number): Promise<User | undefined> {
        return this.users.get(id);
    }

    async createUser(user: User): Promise<void> {
        this.users.set(user.id, user);
    }
}

function validateEmail(email: string): boolean {
    const regex = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
    return regex.test(email);
}
""")
    return file_path


@pytest.fixture
def sample_csharp(temp_dir) -> Path:
    """Create a C# file for testing."""
    file_path = temp_dir / "sample.cs"
    file_path.write_text("""
using System;
using System.Collections.Generic;
using System.Linq;

namespace MyApp
{
    public class User
    {
        public int Id { get; set; }
        public string Name { get; set; }
        public string Email { get; set; }

        public string GetDisplayName()
        {
            return $"{Name} <{Email}>";
        }
    }

    public class UserService
    {
        private readonly IDatabase _database;

        public UserService(IDatabase database)
        {
            _database = database;
        }

        public async Task<User> GetUserAsync(int id)
        {
            return await _database.GetUserAsync(id);
        }

        public async Task<List<User>> GetActiveUsersAsync()
        {
            var users = await _database.GetUsersAsync();
            return users.Where(u => u.IsActive).ToList();
        }
    }
}
""")
    return file_path


@pytest.fixture
def sample_python_imports(temp_dir) -> Path:
    """Create a Python file with various imports."""
    file_path = temp_dir / "imports.py"
    file_path.write_text("""
import os
import sys
from typing import List, Dict
from pathlib import Path
import numpy as np
import pandas as pd
from flask import Flask, request
from .models import User
from .database import Database
from ..utils import helper

def process_data():
    pass
""")
    return file_path


@pytest.fixture
def sample_project_structure(temp_dir) -> Path:
    """Create a sample project structure with multiple files."""
    project = temp_dir / "project"
    project.mkdir()

    # Create auth.py
    (project / "auth.py").write_text("""
import bcrypt
from .models import User

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
""")

    # Create models.py
    (project / "models.py").write_text("""
from dataclasses import dataclass

@dataclass
class User:
    id: int
    username: str
    email: str
""")

    # Create database.py
    (project / "database.py").write_text("""
import sqlite3
from .models import User

class Database:
    def __init__(self, path: str):
        self.conn = sqlite3.connect(path)
""")

    return project
