using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;

namespace YourNamespace.Models
{
    /// <summary>
    /// Represents a unified view model for all assessment types
    /// </summary>
    public class UnifiedAssessmentViewModel
    {
        /// <summary>
        /// Gets or sets the unique identifier for the data entity
        /// </summary>
        public long DataEntityID { get; set; }

        /// <summary>
        /// Gets or sets the assessment item name
        /// </summary>
        [Required(ErrorMessage = "Assessment item is required")]
        public string AssessmentItem { get; set; }

        /// <summary>
        /// Gets or sets the performance review identifier
        /// </summary>
        public long PerformanceReview { get; set; }

        /// <summary>
        /// Gets or sets the employee information
        /// </summary>
        [Required(ErrorMessage = "Employee information is required")]
        public string Employee { get; set; }

        /// <summary>
        /// Gets or sets the assessment date
        /// </summary>
        [Required(ErrorMessage = "Date is required")]
        public DateTime Date { get; set; }

        /// <summary>
        /// Gets or sets the agreed rating
        /// </summary>
        [Range(1, 5, ErrorMessage = "Rating must be between 1 and 5")]
        public long AgreedRating { get; set; }

        /// <summary>
        /// Gets or sets the agreed comments
        /// </summary>
        public string AgreedComments { get; set; }

        /// <summary>
        /// Gets or sets the list of available ratings
        /// </summary>
        public List<Rating> Ratings { get; set; }

        /// <summary>
        /// Gets or sets the assessment type
        /// </summary>
        [Required(ErrorMessage = "Assessment type is required")]
        public string AssessmentType { get; set; }
    }
}