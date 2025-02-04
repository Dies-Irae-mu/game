from django.db import models
from evennia.utils.idmapper.models import SharedMemoryModel
from django.urls import reverse
from evennia.accounts.models import AccountDB
from django.core.files.base import ContentFile
import requests
from urllib.parse import urlparse
import os
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.text import slugify


# Create your models here.

class WikiPage(models.Model):
    """
    Model for storing wiki pages.
    """
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    right_content = models.TextField(
        blank=True,
        null=True,
        help_text="Optional content for the right sidebar. Leave empty to hide."
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Show this article in the featured articles list"
    )
    is_index = models.BooleanField(
        default=False,
        help_text="Use this page as the wiki index page"
    )
    related_to = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='related_from',
        help_text="Select articles that are related to this one"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(
        AccountDB,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_pages',
        help_text="The user who created this page."
    )
    last_editor = models.ForeignKey(
        AccountDB,
        on_delete=models.SET_NULL,
        null=True,
        related_name='edited_pages',
        help_text="The last user to edit this page."
    )
    featured_order = models.IntegerField(default=0)  # For ordering featured articles
    published = models.BooleanField(default=True)

    class Meta:
        app_label = 'wiki'
        verbose_name = "Wiki Page"
        verbose_name_plural = "Wiki Pages"
        ordering = ['title']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """Return the URL for viewing this page on the site."""
        return reverse('wiki:page_detail', kwargs={'slug': self.slug})

    def save(self, current_user=None, *args, **kwargs):
        """Override save to handle meta information and slug creation."""
        if not self.slug:
            self.slug = slugify(self.title)

        is_new = self.pk is None
        
        if is_new and current_user:
            self.creator = current_user
            self.last_editor = current_user
        elif current_user:
            self.last_editor = current_user

        if self.is_index:
            # Unset any other index pages
            WikiPage.objects.filter(is_index=True).exclude(
                pk=self.pk
            ).update(is_index=False)

        super().save(*args, **kwargs)
        
        # Create initial revision if this is a new page
        if is_new and self.creator:
            WikiRevision.objects.create(
                page=self,
                content=self.content,
                editor=self.creator,
                comment="Initial creation"
            )


class WikiRevision(SharedMemoryModel):
    """
    Model for storing wiki page revisions.
    """
    page = models.ForeignKey(
        WikiPage,
        on_delete=models.CASCADE,
        related_name='revisions',
        help_text="The wiki page this revision belongs to."
    )
    content = models.TextField(
        help_text="The content of this revision."
    )
    editor = models.ForeignKey(
        AccountDB,
        on_delete=models.SET_NULL,
        null=True,
        help_text="The user who made this revision."
    )
    edited_at = models.DateTimeField(auto_now_add=True)
    comment = models.CharField(
        max_length=255,
        blank=True,
        help_text="A brief description of the changes made in this revision."
    )

    class Meta:
        app_label = 'wiki'
        verbose_name = "Wiki Revision"
        verbose_name_plural = "Wiki Revisions"
        ordering = ['-edited_at']

    def __str__(self):
        return f"Revision of {self.page.title} at {self.edited_at}"


class FeaturedImage(models.Model):
    """
    Model for storing featured images for wiki pages.
    """
    class Meta:
        app_label = 'wiki'

    page = models.OneToOneField(
        'WikiPage',
        on_delete=models.CASCADE,
        related_name='featured_image'
    )
    image = models.ImageField(
        upload_to='featured/',
        null=True,
        blank=True,
        help_text="Upload or provide URL for background image"
    )
    banner = models.ImageField(
        upload_to='banners/',
        null=True,
        blank=True,
        help_text="Upload or provide URL for banner image"
    )
    show_texture = models.BooleanField(
        default=True,
        help_text="Toggle the texture overlay on/off"
    )

    def get_image_url(self):
        if self.image:
            return self.image.url
        return '/static/wiki/imgs/featured-default.jpg'

    def get_banner_url(self):
        if self.banner:
            return self.banner.url
        return '/static/wiki/imgs/DiesMain.png'

    def download_image(self, url, field_name):
        """Download image from URL and save to ImageField."""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                # Get filename from URL
                filename = os.path.basename(urlparse(url).path)
                if not filename:
                    filename = 'downloaded_image.jpg'
                
                # Save to the appropriate field
                field = getattr(self, field_name)
                field.save(filename, ContentFile(response.content), save=False)
                return True
        except Exception as e:
            print(f"Error downloading image: {e}")
        return False

    def save(self, *args, **kwargs):
        # Check if image or banner fields contain URLs
        if isinstance(self.image, str) and (
            self.image.startswith('http://') or 
            self.image.startswith('https://')
        ):
            self.download_image(self.image, 'image')
        
        if isinstance(self.banner, str) and (
            self.banner.startswith('http://') or 
            self.banner.startswith('https://')
        ):
            self.download_image(self.banner, 'banner')
        
        super().save(*args, **kwargs)
