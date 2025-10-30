"""Shared test fixtures for EF Core Analysis tests."""

import shutil
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_dbcontext(temp_dir) -> Path:
    """Create a sample DbContext file."""
    file_path = temp_dir / "ApplicationDbContext.cs"
    file_path.write_text("""
using Microsoft.EntityFrameworkCore;
using MyApp.Models;

namespace MyApp.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options)
            : base(options)
        {
        }

        public DbSet<User> Users { get; set; }
        public DbSet<Order> Orders { get; set; }
        public DbSet<Product> Products { get; set; }

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<User>(entity =>
            {
                entity.HasKey(e => e.Id);
                entity.HasIndex(e => e.Email).IsUnique();
                entity.Property(e => e.Name).IsRequired().HasMaxLength(100);
            });

            modelBuilder.Entity<Order>(entity =>
            {
                entity.HasOne(o => o.User)
                    .WithMany(u => u.Orders)
                    .HasForeignKey(o => o.UserId);
            });

            base.OnModelCreating(modelBuilder);
        }
    }
}
""")
    return file_path


@pytest.fixture
def sample_entity_simple(temp_dir) -> Path:
    """Create a simple entity model."""
    file_path = temp_dir / "User.cs"
    file_path.write_text("""
using System;
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }

        [Required]
        [MaxLength(100)]
        public string Name { get; set; }

        [Required]
        [EmailAddress]
        public string Email { get; set; }

        public DateTime CreatedAt { get; set; }

        public bool IsActive { get; set; }
    }
}
""")
    return file_path


@pytest.fixture
def sample_entity_with_relationships(temp_dir) -> Path:
    """Create an entity model with navigation properties."""
    file_path = temp_dir / "Order.cs"
    file_path.write_text("""
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace MyApp.Models
{
    public class Order
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public int UserId { get; set; }

        [ForeignKey(nameof(UserId))]
        public User User { get; set; }

        public DateTime OrderDate { get; set; }

        public decimal TotalAmount { get; set; }

        public ICollection<OrderItem> OrderItems { get; set; }
    }
}
""")
    return file_path


@pytest.fixture
def sample_entity_invalid(temp_dir) -> Path:
    """Create an entity model with validation issues."""
    file_path = temp_dir / "InvalidEntity.cs"
    file_path.write_text("""
using System.Collections.Generic;

namespace MyApp.Models
{
    public class InvalidEntity
    {
        // Missing primary key
        public string Name { get; set; }

        public ICollection<Order> Orders { get; set; }  // Missing foreign key
    }
}
""")
    return file_path


@pytest.fixture
def sample_linq_queries(temp_dir) -> Path:
    """Create a repository file with various LINQ queries."""
    file_path = temp_dir / "UserRepository.cs"
    file_path.write_text("""
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Models;

namespace MyApp.Repositories
{
    public class UserRepository
    {
        private readonly ApplicationDbContext _context;

        public UserRepository(ApplicationDbContext context)
        {
            _context = context;
        }

        // Good: Async with Include
        public async Task<User> GetUserByIdAsync(int id)
        {
            return await _context.Users
                .Include(u => u.Orders)
                .FirstOrDefaultAsync(u => u.Id == id);
        }

        // Issue: Synchronous ToList
        public List<User> GetActiveUsers()
        {
            return _context.Users
                .Where(u => u.IsActive)
                .ToList();
        }

        // Issue: Potential N+1 problem
        public async Task<List<Order>> GetUserOrdersAsync(int userId)
        {
            var user = await _context.Users.FirstOrDefaultAsync(u => u.Id == userId);
            return user.Orders.ToList();
        }

        // Good: Proper filtering and async
        public async Task<List<User>> GetUsersByEmailAsync(string email)
        {
            return await _context.Users
                .Where(u => u.Email.Contains(email))
                .OrderBy(u => u.Name)
                .ToListAsync();
        }

        // Issue: FirstOrDefault without Where
        public User GetFirstUser()
        {
            return _context.Users.FirstOrDefault();
        }
    }
}
""")
    return file_path


@pytest.fixture
def sample_linq_no_issues(temp_dir) -> Path:
    """Create a repository file with optimized LINQ queries."""
    file_path = temp_dir / "OptimizedRepository.cs"
    file_path.write_text("""
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Models;

namespace MyApp.Repositories
{
    public class OptimizedRepository
    {
        private readonly ApplicationDbContext _context;

        public OptimizedRepository(ApplicationDbContext context)
        {
            _context = context;
        }

        public async Task<User> GetUserByIdAsync(int id)
        {
            return await _context.Users
                .Include(u => u.Orders)
                .ThenInclude(o => o.OrderItems)
                .FirstOrDefaultAsync(u => u.Id == id);
        }

        public async Task<List<User>> GetActiveUsersAsync()
        {
            return await _context.Users
                .Where(u => u.IsActive)
                .OrderBy(u => u.Name)
                .ToListAsync();
        }
    }
}
""")
    return file_path


@pytest.fixture
def sample_project_structure(temp_dir) -> Path:
    """Create a project structure with multiple files."""
    project_dir = temp_dir / "SampleProject"
    project_dir.mkdir()

    # Models directory
    models_dir = project_dir / "Models"
    models_dir.mkdir()

    # User.cs
    (models_dir / "User.cs").write_text("""
using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string Name { get; set; }
        [Required]
        public string Email { get; set; }

        public ICollection<Order> Orders { get; set; }
    }
}
""")

    # Order.cs
    (models_dir / "Order.cs").write_text("""
using System;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;

namespace MyApp.Models
{
    public class Order
    {
        [Key]
        public int Id { get; set; }

        public int UserId { get; set; }
        [ForeignKey(nameof(UserId))]
        public User User { get; set; }

        public DateTime OrderDate { get; set; }
    }
}
""")

    # Product.cs
    (models_dir / "Product.cs").write_text("""
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class Product
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public string Name { get; set; }
        public decimal Price { get; set; }
        public int CategoryId { get; set; }
    }
}
""")

    # Data directory
    data_dir = project_dir / "Data"
    data_dir.mkdir()

    # ApplicationDbContext.cs
    (data_dir / "ApplicationDbContext.cs").write_text("""
using Microsoft.EntityFrameworkCore;
using MyApp.Models;

namespace MyApp.Data
{
    public class ApplicationDbContext : DbContext
    {
        public DbSet<User> Users { get; set; }
        public DbSet<Order> Orders { get; set; }
        public DbSet<Product> Products { get; set; }
    }
}
""")

    # Repositories directory
    repos_dir = project_dir / "Repositories"
    repos_dir.mkdir()

    # UserRepository.cs with queries
    (repos_dir / "UserRepository.cs").write_text("""
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Models;

namespace MyApp.Repositories
{
    public class UserRepository
    {
        private readonly ApplicationDbContext _context;

        public async Task<User> GetByEmailAsync(string email)
        {
            return await _context.Users
                .Where(u => u.Email == email)
                .FirstOrDefaultAsync();
        }

        public async Task<List<User>> GetUsersByDateAsync(DateTime date)
        {
            return await _context.Users
                .Where(u => u.CreatedAt > date)
                .OrderBy(u => u.CreatedAt)
                .ToListAsync();
        }
    }
}
""")

    # OrderRepository.cs with queries
    (repos_dir / "OrderRepository.cs").write_text("""
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Models;

namespace MyApp.Repositories
{
    public class OrderRepository
    {
        private readonly ApplicationDbContext _context;

        public async Task<List<Order>> GetOrdersByDateAsync(DateTime date)
        {
            return await _context.Orders
                .Where(o => o.OrderDate >= date)
                .OrderBy(o => o.OrderDate)
                .ToListAsync();
        }
    }
}
""")

    # ProductService.cs with queries
    (repos_dir / "ProductService.cs").write_text("""
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using MyApp.Data;
using MyApp.Models;

namespace MyApp.Services
{
    public class ProductService
    {
        private readonly ApplicationDbContext _context;

        public async Task<List<Product>> GetByCategoryAsync(int categoryId)
        {
            return await _context.Products
                .Where(p => p.CategoryId == categoryId)
                .OrderBy(p => p.Name)
                .ToListAsync();
        }
    }
}
""")

    return project_dir


@pytest.fixture
def sample_model_old(temp_dir) -> Path:
    """Create an old version of a model for migration testing."""
    file_path = temp_dir / "User.old.cs"
    file_path.write_text("""
using System;
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public string Name { get; set; }

        public DateTime CreatedAt { get; set; }
    }
}
""")
    return file_path


@pytest.fixture
def sample_model_new(temp_dir) -> Path:
    """Create a new version of a model for migration testing."""
    file_path = temp_dir / "User.new.cs"
    file_path.write_text("""
using System;
using System.ComponentModel.DataAnnotations;

namespace MyApp.Models
{
    public class User
    {
        [Key]
        public int Id { get; set; }

        [Required]
        public string Name { get; set; }

        [Required]
        [EmailAddress]
        public string Email { get; set; }

        public DateTime CreatedAt { get; set; }

        public bool IsActive { get; set; }
    }
}
""")
    return file_path
