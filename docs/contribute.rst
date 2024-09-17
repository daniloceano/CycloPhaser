Contribute
==========

We welcome contributions to CycloPhaser! Whether you're fixing a bug, adding a new feature, or improving documentation, here's how you can contribute:

1. **Fork the Repository**
   
   - Visit the [CycloPhaser GitHub repository](https://github.com/daniloceano/CycloPhaser).
   - Click the "Fork" button at the top-right corner of the repository page to create a copy of the repository in your GitHub account.

2. **Clone Your Fork**

   - Open your terminal and clone your forked repository to your local machine:
   
     .. code-block:: bash
   
        git clone https://github.com/your-username/CycloPhaser.git
   
   - Navigate into the cloned repository:
   
     .. code-block:: bash
   
        cd CycloPhaser

3. **Create a Branch**

   - Before making any changes, create a new branch to keep your work organized. Use a descriptive name for your branch based on the feature or fix you're working on:
   
     .. code-block:: bash
   
        git checkout -b feature/your-feature-name

4. **Make Your Changes**

   - Implement your changes, whether you're fixing a bug, adding new functionality, or improving documentation.
   - Make sure to follow any coding conventions used in the project (e.g., naming conventions, code formatting).
   - If you're adding new features or modifying existing ones, consider writing or updating tests to ensure code quality.
   - To run tests, follow these steps:
   
     .. code-block:: bash
   
        # Install dependencies
        pip install -r requirements.txt
   
        # Run tests
        pytest tests/

5. **Commit Your Changes**

   - After making your changes, commit them with a descriptive commit message:
   
     .. code-block:: bash
   
        git add .
        git commit -m "Description of your changes"

6. **Push to Your Fork**

   - Push your changes to your forked repository on GitHub:
   
     .. code-block:: bash
   
        git push origin feature/your-feature-name

7. **Submit a Pull Request**

   - Go to your forked repository on GitHub and click the "Compare & Pull Request" button.
   - Ensure that your pull request is being submitted to the **main** branch of the original repository.
   - In the pull request description, explain the changes you’ve made and provide any relevant context, such as what issue you’re addressing or what feature you're adding.

8. **Respond to Feedback**

   - Your pull request will be reviewed by the maintainers of CycloPhaser. If any changes are requested, make the necessary updates and push them to your branch.
   - Keep an eye on your pull request and respond to any comments or questions from reviewers.

9. **Celebrate!**

   - Once your pull request is merged, congratulations! You’ve contributed to CycloPhaser. 🎉

### Additional Notes

- **Issues**: If you encounter any problems or have ideas for improvements, please check the [issues page](https://github.com/daniloceano/CycloPhaser/issues) or open a new issue.
- **Documentation**: Contributions to documentation are as important as code! If you find any unclear instructions, please help us by submitting improvements.
- **Code Style**: Make sure your code adheres to the project's style guidelines. You can use tools like `flake8` and `black` to check and format your code:
  
  .. code-block:: bash
  
     pip install flake8 black
     flake8 .
     black .

Thank you for helping make CycloPhaser better for everyone!
